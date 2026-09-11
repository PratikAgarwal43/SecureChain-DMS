import json
from securechain_security.hash_service import HashService
from securechain_security.key_manager import KeyManager, LocalKMSProvider
from securechain_security.encryption_service import EncryptionService
from securechain_security.chain_engine import ChainEngine
from securechain_security.vault_router import VaultRouter

def run_demo():
    print("=== SecureChain DMS Security Layer Demo ===\n")
    
    # 1. Initialize the security engines
    print("[*] Initializing Security Modules...")
    hash_service = HashService()
    key_manager = KeyManager(kms_provider=LocalKMSProvider())
    encryption_service = EncryptionService(key_manager, hash_service)
    chain_engine = ChainEngine(hash_service)
    vault_router = VaultRouter(encryption_service, chain_engine)
    
    # 2. Simulate a sensitive document upload
    case_id = "CASE-2026-DELHI-001"
    document_id = "DOC-FIR-999"
    officer_id = "OFFICER-SHREYASH"
    
    original_text = "CONFIDENTIAL FIR: Suspect was seen near the crime scene at 11:30 PM."
    plaintext_bytes = original_text.encode('utf-8')
    
    print(f"\n[*] Officer {officer_id} is uploading an FIR for case {case_id}")
    print(f"    Original Document Text: '{original_text}'")
    
    # 3. Process the upload through the Two-Vault Router
    print("\n[*] Encrypting and Hashing (Routing to Vaults)...")
    vault_package = vault_router.process_upload(
        plaintext=plaintext_bytes,
        document_id=document_id,
        case_id=case_id,
        officer_id=officer_id
    )
    
    # --- VAULT 1: DATABASE ---
    print("\n" + "="*50)
    print("[VAULT 1 - DATABASE] receives this JSON:")
    print("   Contains hashes, metadata, and encrypted keys. NO readable document.")
    print("="*50)
    metadata_copy = vault_package.vault1_metadata.copy()
    print(json.dumps(metadata_copy, indent=4))
    
    # --- VAULT 2: OBJECT STORAGE ---
    print("\n" + "="*50)
    print("[VAULT 2 - OBJECT STORAGE] receives these locked bytes:")
    print("   Contains NO keys and NO metadata. Just scrambled ciphertext.")
    print("="*50)
    print(f"Ciphertext (Hex): {vault_package.vault2_blob.hex()[:60]}... (truncated)")
    
    # 4. Simulate a Court Retrieval
    print("\n" + "="*50)
    print("[COURT RETRIEVAL] Unlocking the document...")
    print("="*50)
    
    recovered_bytes = vault_router.process_retrieval(
        vault1_metadata=vault_package.vault1_metadata,
        vault2_blob=vault_package.vault2_blob
    )
    
    recovered_text = recovered_bytes.decode('utf-8')
    print(f"[*] Decrypted successfully!")
    print(f"    Recovered Document Text: '{recovered_text}'\n")
    
    if original_text == recovered_text:
        print("✅ SUCCESS: The immutability and confidentiality pipeline works perfectly!")

if __name__ == "__main__":
    run_demo()
