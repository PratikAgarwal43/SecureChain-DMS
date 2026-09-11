import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import json
import os


class QwenDocumentParser:
    def __init__(self):
        self.model_id = "Qwen/Qwen2-VL-7B-Instruct"
        print(f"[+] Initializing Memory-Optimized Dual-T4 Ingestion Engine: {self.model_id}")

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Higher resolution -> much better OCR accuracy on handwritten/stamped
        # fields (district, PS, complainant, accused). Correctness matters more
        # than raw speed for legal documents.
        self.processor = AutoProcessor.from_pretrained(
            self.model_id,
            min_pixels=256 * 256,
            max_pixels=768 * 768
        )

    # ------------------------------------------------------------------
    # Required columns — tumhari sample FIR (Bihar Police, BNSS/BNS format)
    # ke fields se directly liye gaye hain. Note the IMPORTANT distinction:
    #   - complainant_name        = jisne FIR di / informant (e.g. Ajay Sharma)
    #   - fir_registered_by       = jisne FIR likhi/register ki, station-house
    #                                officer (signature block, e.g. Amrit Kumar Sah, SHO)
    #   - investigating_officer   = jise case investigate karne ke liye
    #                                DIRECT kiya gaya (e.g. Vijay, ASI, vij261167)
    # These are three different people on a real FIR — don't merge them.
    # ------------------------------------------------------------------
    FIR_PROMPT = """
    You are an expert legal-document extraction layer inside SecureChain DMS,
    specialised in Indian Police FIRs filed under BNSS/BNS (2023 Indian
    penal framework). The attached image is a scanned FIR or an attached
    complaint letter. It may be in Hindi, English, or a mix, and may be
    handwritten, stamped, watermarked, or low quality.

    CRITICAL INSTRUCTION: Regardless of source language, translate and write
    EVERY extracted value into clear English. Do not leave any field in
    Hindi/Devanagari script — transliterate names/places into English
    spelling, and translate all descriptive/narrative text into English.

    ANTI-HALLUCINATION RULE (most important rule — read carefully): This is
    a real legal document. Fabricating information is worse than leaving a
    field empty. Only output a value if you can actually see it written on
    the page. Never invent names, vehicle numbers, amounts, phone numbers,
    or a backstory that "sounds like" a typical FIR. If a field is blurry,
    cut off, or not present on this specific page, output null for it. Do
    not blend details from a different case or example you may recall —
    describe only what is physically visible in THIS image.

    Extract STRICT JSON only, matching this exact schema (use the JSON
    literal null, never a description or placeholder, for anything not
    clearly visible on this page):

    {
      "district": "string or null",
      "police_station": "string or null",
      "fir_number": "string or null",
      "case_number": "string or null",
      "year": "string or null",
      "date_of_fir": "string or null (DD/MM/YYYY)",
      "time_of_fir": "string or null (HH:MM)",
      "acts_and_sections": ["array of strings, or empty array"],
      "date_of_occurrence": "string or null (DD/MM/YYYY)",
      "place_of_occurrence": "string or null",
      "complainant_name": "string or null (the informant who filed the FIR — never a police officer)",
      "complainant_father_or_husband_name": "string or null",
      "complainant_address": "string or null",
      "complainant_phone": "string or null",
      "accused_details": [
        {"name": "string", "alias": "string or null", "father_or_husband_name": "string or null", "address": "string or null"}
      ],
      "items_of_interest": "string or null",
      "total_value_inr": "string or null",
      "fir_registered_by": "string or null (name + rank + ID of the officer who signed/registered the FIR)",
      "investigating_officer": "string or null (name + rank + ID of the officer directed to investigate)",
      "fir_description_english": "string or null"
    }

    RULES FOR fir_description_english specifically:
    - Only fill this if THIS page contains an actual free-text narrative /
      complaint story (e.g. a "First Information contents" section, or an
      attached complaint letter).
    - If this page is only a tabular form with field labels and no free-text
      story, set it to null. Do NOT invent, guess, or summarize a story that
      is not actually written on the page.
    - Never copy any of these instructions into the output.
    - Keep it under 120 words, and never repeat the same sentence twice.

    Here is a FORMAT-ONLY worked example, showing HOW to map fields from a
    typical Bihar Police FIR (BNSS format) into the JSON schema. The values
    below are placeholders (marked with < >) — they are NOT real data and
    must NEVER appear in your actual output:

    Example source text pattern seen on this type of document (Hindi + English):
    "District: <district in Hindi>, P.S.: <police station in Hindi>, FIR
    No.: <long number>, Date and Time of FIR: <date> <time>, Act: भारतीय
    न्याय संहिता (बीएनएस) 2023, Sections: <section numbers>, Date of
    occurrence: <date>, Complainant Name: <name in Hindi>, Father's Name:
    <name in Hindi>, Address: <address in Hindi>, Mobile: <number>, Accused:
    <name(s) in Hindi with relation/address>, Contents: <offence type and
    narrative in Hindi>, Action Taken -> Directed (Name of I.O.): <IO name>,
    Rank: <rank in Hindi>, No.: <officer id>. Signature block: Officer in
    charge of Police Station — <SHO name>, Rank: <rank in Hindi>, No.:
    <officer id>."

    Format pattern for the extraction (structure only — fill with what YOU
    actually read from the image, never these placeholder tokens):
    {
      "district": "<English translation of district>",
      "police_station": "<English translation of PS name>",
      "fir_number": "<the long FIR number from the image>",
      "case_number": "<PS case no. from a stamp, if visible>",
      "year": "<year>",
      "date_of_fir": "<DD/MM/YYYY from the image>",
      "time_of_fir": "<HH:MM from the image>",
      "acts_and_sections": ["BNS Section <n>", "..."],
      "date_of_occurrence": "<DD/MM/YYYY from the image>",
      "place_of_occurrence": "<English translation of the location text>",
      "complainant_name": "<English transliteration of the informant's name — NOT a police officer>",
      "complainant_father_or_husband_name": "<English transliteration>",
      "complainant_address": "<English translation>",
      "complainant_phone": "<number from the image>",
      "accused_details": [
        {"name": "<English transliteration>", "alias": "<role, e.g. vehicle owner>", "father_or_husband_name": "<or null>", "address": "<English translation>"}
      ],
      "items_of_interest": "<English translation of stolen/seized property description>",
      "total_value_inr": "<amount from the image, if stated>",
      "fir_registered_by": "<name + rank + ID of the officer who signed/registered the FIR>",
      "investigating_officer": "<name + rank + ID of the officer directed to investigate>",
      "fir_description_english": "<a full English narrative summary built from what THIS image actually says>"
    }

    HARD RULE: Every value in your final answer must come from pixels you
    can actually see in the image(s) provided in THIS request. If you
    cannot read a field clearly, use the JSON literal null (no quotes) —
    never write the word "null" as a quoted string, and never guess or
    reuse any name, number, date, or address from this instructions block,
    since none of it belongs to the document you are now analyzing.

    Now extract the fields from the ACTUAL document in the image(s) above,
    following this exact schema and mapping logic. Return ONLY valid,

    parseable JSON. No markdown fences, no commentary, no notes.
    """

    def extract_document(self, image_path: str) -> dict:
        """Single-page extraction (kept for single-image use cases)."""
        return self.extract_document_batch([image_path])

    def extract_document_batch(self, image_paths: list) -> dict:
        """
        SPEED FIX: instead of calling the model once PER PAGE (N slow generate()
        calls, each with its own fixed overhead), send ALL pages of the document
        as multiple images in a SINGLE message. Qwen2-VL supports multi-image
        input natively, so the model reads every page together and returns ONE
        consolidated JSON directly — this cuts an 8-page document from 8 model
        calls down to 1.
        """
        valid_paths = [p for p in image_paths if os.path.exists(p)]
        if not valid_paths:
            return {"error": "No valid image paths provided."}

        multi_page_note = ""
        if len(valid_paths) > 1:
            multi_page_note = f"""
    NOTE: The following {len(valid_paths)} images are ALL PAGES of the SAME
    document (in page order). Some information may repeat across pages
    (e.g. an attached letter restating the FIR content) — combine everything
    into ONE single consolidated JSON object covering the whole document.
    Do not return one JSON per page; return exactly one merged JSON object.
    """

        content = [{"type": "image", "image": p} for p in valid_paths]
        content.append({"type": "text", "text": multi_page_note + self.FIR_PROMPT})

        messages = [{"role": "user", "content": content}]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=768)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text_list = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )

        raw_output = output_text_list[0] if output_text_list else ""

        try:
            cleaned_json = raw_output.strip().replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(cleaned_json)
            return self._normalize_null_strings(parsed_data)
        except Exception as err:
            return {
                "error": "Structural formatting variance caught during extraction inference.",
                "raw_payload": raw_output,
                "exception": str(err)
            }

    @staticmethod
    def _normalize_null_strings(value):
        """
        Defensive fix: the model sometimes writes the literal string "null"
        instead of the JSON null token. Recursively convert any such string
        (case-insensitive, also handles "n/a", "none", "not visible", "") into
        real None so downstream code treats it as genuinely missing data.
        """
        NULL_LIKE = {"null", "n/a", "na", "none", "not visible", "not available", ""}
        if isinstance(value, dict):
            return {k: QwenDocumentParser._normalize_null_strings(v) for k, v in value.items()}
        if isinstance(value, list):
            return [QwenDocumentParser._normalize_null_strings(v) for v in value]
        if isinstance(value, str) and value.strip().lower() in NULL_LIKE:
            return None
        return value

    # ------------------------------------------------------------------
    # Multi-page merge: FIR jaisi documents mein kai page hote hain
    # (FIR form + attached complaint letter). Har page alag extract hota
    # hai, fir ek consolidated record mein merge kiya jaata hai.
    # ------------------------------------------------------------------
    def merge_page_results(self, page_results: list) -> dict:
        merged = {}
        accused_all = []
        candidate_summaries = []

        # phrases that indicate the model echoed our own instructions instead
        # of real document content -> any summary containing these is discarded
        SUSPICIOUS_ECHO_PHRASES = [
            "full narrative/complaint content",
            "complete english summary",
            "do not omit facts",
            "never invent",
            "anti-hallucination",
        ]

        scalar_fields = [
            "district", "police_station", "fir_number", "case_number", "year",
            "date_of_fir", "time_of_fir", "date_of_occurrence",
            "place_of_occurrence", "complainant_name", "complainant_father_or_husband_name",
            "complainant_address", "complainant_phone", "items_of_interest",
            "total_value_inr", "fir_registered_by", "investigating_officer"
        ]
        for field in scalar_fields:
            merged[field] = None

        merged["acts_and_sections"] = []

        for page in page_results:
            if not isinstance(page, dict) or "error" in page:
                continue

            for field in scalar_fields:
                if not merged.get(field) and page.get(field):
                    merged[field] = page[field]

            for section in page.get("acts_and_sections", []) or []:
                if section and section not in merged["acts_and_sections"]:
                    merged["acts_and_sections"].append(section)

            for accused in page.get("accused_details", []) or []:
                # drop junk entries where every field is empty/None -> nothing
                # real was actually read on that page
                if not accused or not any(accused.get(k) for k in
                                           ["name", "alias", "father_or_husband_name", "address"]):
                    continue
                if accused not in accused_all:
                    accused_all.append(accused)

            summary = page.get("fir_description_english")
            if summary and isinstance(summary, str):
                lowered = summary.lower()
                if any(phrase in lowered for phrase in SUSPICIOUS_ECHO_PHRASES):
                    continue  # looks like an echoed instruction, not real content
                candidate_summaries.append(summary.strip())

        merged["accused_details"] = accused_all

        # ACCURACY FIX: don't blindly concatenate every page's summary — different
        # pages can produce conflicting/hallucinated narratives, and joining them
        # with spaces produces a garbled mixed-up story. Instead, pick the single
        # longest surviving candidate (most detailed real narrative), which is
        # usually the actual "First Information contents" / complaint-letter page.
        if candidate_summaries:
            merged["fir_description_english"] = max(candidate_summaries, key=len)
        else:
            merged["fir_description_english"] = None

        return merged
