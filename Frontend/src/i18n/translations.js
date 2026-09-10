/**
 * Complete Bilingual Localization Dictionary (English / हिन्दी)
 * Sitewide coverage: navbar, mega-menus, sidebars, dashboard widgets,
 * forms, citizen portal, status badges, buttons, tooltips, footer, etc.
 */

export const translations = {
  en: {
    // Top Micro-strip
    govtOfIndia: "GOVERNMENT OF INDIA",
    ministryHeader: "Ministry of Home Affairs — National Investigation Records System",
    helpline: "National Emergency & Investigation Helpline: 112",
    contrastStandard: "Standard",
    contrastHigh: "High Contrast",
    fontSize: "Font Size",

    // Header & Brand
    appTitleHindi: "राष्ट्रीय सुरक्षित दस्तावेज़ प्रबंधन प्रणाली",
    appTitleEnglish: "SecureChain DMS — National Investigation Records System",
    appSubtitle: "Ministry of Home Affairs, Government of India",

    // Navigation Items & Dropdowns
    navHome: "Home",
    navDashboard: "Dashboard",
    navCases: "Cases & Evidence",
    navAllCases: "All Case Records",
    navActiveCases: "Active Investigations",
    navPendingReviews: "Pending Quorum Reviews",
    navClosedCases: "Closed Records",
    navUpload: "Upload Record",
    navApprovals: "Quorum Approvals",
    navAudit: "Audit Log",
    navHelpAndLegal: "Legal & Guidelines",
    navAbout: "About SecureChain",
    navLegalActs: "Evidence Act & Statutory Rules",
    navCitizenHelp: "Citizen Guidance & FAQs",
    navContact: "Official Contacts",
    navTrackRecords: "Track My Records",
    officerLogin: "Officer Login",
    logout: "Logout",
    roleSelector: "Switch Role",

    // Homepage / Portal Selector
    heroBadge: "Official Government of India Document Custody Platform",
    heroTitlePrefix: "SecureChain DMS —",
    heroTitleHighlight: "Tamper-Evident Records",
    heroTitleSuffix: "for Police & Judicial Investigation",
    heroSubtitle: "A national investigation records system for FIRs, chargesheets, and forensic reports. Built so no single official can alter a legal record without instant notification and multi-officer approval.",
    heroCtaDashboard: "Access Case Dashboard",
    heroCtaLearn: "Explore Public Guidance",

    // Portal Cards
    portalSelectorTitle: "Select Departmental Gateway",
    portalSelectorSubtitle: "Dedicated gateways for investigating officers, judicial authorities, forensic laboratories, and citizens.",
    
    cardPoliceTitle: "Police / Investigating Officer",
    cardPoliceDesc: "Register formal FIRs, upload investigation evidence, request supplementary updates, and maintain strict custody logs.",
    cardPoliceBtn: "Police Portal Login",

    cardJudicialTitle: "Judicial Authority",
    cardJudicialDesc: "Review case evidence submitted to court, verify record integrity mathematically, and cast consensus votes in review queues.",
    cardJudicialBtn: "Judicial Portal Login",

    cardForensicTitle: "Forensic Expert",
    cardForensicDesc: "Upload laboratory examination reports, classify analysis sensitivity, record physical sample seals, and review technical quorums.",
    cardForensicBtn: "Forensic Lab Login",

    cardCitizenTitle: "Citizen — Track My Records",
    cardCitizenDesc: "Check real-time status of your registered FIR or complaint. Plain-language updates with secure OTP verification.",
    cardCitizenBtn: "Track Records",

    // Citizen Portal
    citizenLoginTitle: "Citizen Record Portal",
    citizenLoginSubtitle: "Track the status of your registered police report or official complaint.",
    tabMobileNumber: "By Mobile Number",
    tabAckNumber: "By Acknowledgement / FIR Number",
    mobileNumberLabel: "Registered Mobile Number",
    mobilePlaceholder: "Enter 10-digit mobile number",
    ackNumberLabel: "Acknowledgement / Complaint Number",
    ackPlaceholder: "e.g. ACK-2024-88412 or FIR-2024-ND-0842",
    sendOtpBtn: "Send Verification Code",
    verifyAndLoginBtn: "Verify & View Records",
    demoCitizenNotice: "Demo: Mobile 9876543210 or Ack ACK-2024-88412 with OTP 123456",
    autoLogoutWarning: "Session expires in",
    autoLogoutNotice: "For security, citizen sessions automatically time out after 10 minutes of inactivity.",
    myRecordsHeading: "My Registered Complaints & Cases",
    myRecordsSubheading: "Official record custody status provided by the Ministry of Home Affairs",
    noRecordsFound: "No records found matching your registered details.",
    dateFiled: "Date Registered",
    currentStatus: "Status",
    stationFiled: "Police Station",
    viewDetails: "View Summary",

    // Plain Language Status (Citizen Facing)
    statusUnderInvestigation: "Under Investigation",
    statusUpdatePending: "Update Pending Review",
    statusApprovedLocked: "Verified & Sealed",
    statusClosed: "Case Closed",

    // Dashboards Common
    dashboardHeading: "Case Dashboard",
    dashboardSubheading: "National Investigation Documents Ledger • Verified Custody",
    newDocumentBtn: "+ New Document",
    searchPlaceholder: "Search by FIR No, Title, Police Station, or Accused...",
    statusFilterLabel: "Status",
    filterAll: "All Records",
    filterLocked: "Locked (Official)",
    filterPending: "Pending Approval",
    filterRejected: "Rejected",
    showingCount: "Showing records",

    // Police Dashboard Widgets
    policeWidgetActiveCases: "My Active Cases",
    policeWidgetPendingEdits: "My Pending Edit Requests",
    policeWidgetCustodyTracker: "Chain of Custody Tracker",
    policeWidgetCustodyDesc: "Chronological custody handoffs recorded in the ledger:",
    policeNotificationTitle: "Active Quorum Notification",
    policeNotificationBody: "Your supplementary amendment on {firNo} requires supervisory approval.",

    // Judicial Dashboard Widgets
    judicialWidgetPendingVerify: "Cases Submitted for Court Verification",
    judicialWidgetHashTool: "Evidence Integrity Verification Tool",
    judicialWidgetHashDesc: "Select an evidence document to verify its cryptographic ledger seal against the original court submission.",
    judicialWidgetDeAnon: "De-anonymize Request (Audit Authority)",
    judicialWidgetDeAnonDesc: "Statutory disclosure of an anonymous reviewer's identity. Requires typed judicial justification and is permanently logged.",
    judicialWidgetQueue: "Judicial Approval Queue",
    verifyHashBtn: "Verify Integrity",
    simulateTamperBtn: "Simulate Mismatched Hash",
    matchSuccess: "MATCH — INTACT: Evidence matches original submission. Zero unauthorized alteration.",
    mismatchError: "MISMATCH — INTEGRITY VIOLATION: File contents do not match the sealed ledger hash!",

    // Forensic Dashboard Widgets
    forensicWidgetAwaiting: "Reports Awaiting Seal",
    forensicWidgetOcrQueue: "OCR & Content Analysis Queue",
    forensicWidgetSampleCustody: "Physical & Digital Sample Custody",
    forensicWidgetPendingQuorum: "My Pending Quorum Reviews",
    confirmAndSealBtn: "Confirm & Seal Hash",

    // Quorum Screen
    quorumHeading: "Approval Status",
    quorumSubheading: "Multi-officer independent review queue",
    quorumThresholdLabel: "approvals received",
    quorumRequesterBlocked: "Requester cannot approve own request (Server Enforced)",
    castVoteApprove: "Approve Update",
    castVoteReject: "Reject Update",
    commentsLabel: "Supervisory Review Comments",
    consensusAchieved: "Quorum threshold achieved. Record permanently updated.",

    // WORM Audit Log
    auditHeading: "WORM Audit Log",
    auditSubheading: "Write-Once Read-Many record history. Update and delete operations are strictly prohibited.",
    auditAppendOnlyNotice: "Append-Only Law: Entries are permanently recorded with chronological verification.",
    auditVerifyAllBtn: "Verify Ledger Integrity",
    auditSimulateTamper: "Simulate Tampering",
    auditResetBtn: "Restore Ledger",

    // Status Badges
    badgeLocked: "Locked",
    badgePendingQuorum: "Pending Quorum",
    badgeRejected: "Rejected",
    badgeApproved: "Approved",

    // Footer
    footerManagedBy: "Website Content Managed by Ministry of Home Affairs, Government of India.",
    footerHostedBy: "Hosted by National Informatics Centre (NIC).",
    footerPolicyPrivacy: "Privacy Policy",
    footerPolicyTerms: "Terms of Record Custody",
    footerPolicyHyperlink: "Hyperlinking Policy",
    footerPolicyCopyright: "Copyright Statement",
    footerPolicyAccessibility: "Accessibility Statement"
  },

  hi: {
    // Top Micro-strip
    govtOfIndia: "भारत सरकार",
    ministryHeader: "गृह मंत्रालय — राष्ट्रीय जांच दस्तावेज़ प्रणाली",
    helpline: "राष्ट्रीय आपातकालीन एवं जांच हेल्पलाइन: 112",
    contrastStandard: "सामान्य",
    contrastHigh: "उच्च कंट्रास्ट",
    fontSize: "फ़ॉन्ट आकार",

    // Header & Brand
    appTitleHindi: "राष्ट्रीय सुरक्षित दस्तावेज़ प्रबंधन प्रणाली",
    appTitleEnglish: "SecureChain DMS — National Investigation Records System",
    appSubtitle: "गृह मंत्रालय, भारत सरकार",

    // Navigation Items & Dropdowns
    navHome: "मुख्य पृष्ठ",
    navDashboard: "डैशबोर्ड",
    navCases: "प्रकरण एवं साक्ष्य",
    navAllCases: "सभी प्रकरण अभिलेख",
    navActiveCases: "सक्रिय जांच",
    navPendingReviews: "लंबित कोरम समीक्षा",
    navClosedCases: "निपटारे किए गए प्रकरण",
    navUpload: "दस्तावेज़ अपलोड",
    navApprovals: "कोरम अनुमोदन",
    navAudit: "ऑडिट लॉग",
    navHelpAndLegal: "कानूनी एवं दिशानिर्देश",
    navAbout: "प्रणाली परिचय",
    navLegalActs: "साक्ष्य अधिनियम व वैधानिक नियम",
    navCitizenHelp: "नागरिक मार्गदर्शन व प्रश्नोत्तरी",
    navContact: "आधिकारिक संपर्क",
    navTrackRecords: "अभिलेख स्थिति जानें",
    officerLogin: "अधिकारी लॉगिन",
    logout: "लॉगआउट",
    roleSelector: "भूमिका बदलें",

    // Homepage / Portal Selector
    heroBadge: "भारत सरकार की आधिकारिक दस्तावेज़ अभिरक्षा प्रणाली",
    heroTitlePrefix: "SecureChain DMS —",
    heroTitleHighlight: "अपरिवर्तनीय कानूनी साक्ष्य",
    heroTitleSuffix: "पुलिस व न्यायिक जांच हेतु राष्ट्रीय मंच",
    heroSubtitle: "प्राथमिकी (FIR), आरोप पत्र एवं वैज्ञानिक साक्ष्यों के प्रबंधन हेतु सुरक्षित राष्ट्रीय प्रणाली। किसी भी कानूनी अभिलेख को बिना बहु-अधिकारी अनुमोदन के बदला नहीं जा सकता।",
    heroCtaDashboard: "प्रकरण डैशबोर्ड पर जाएं",
    heroCtaLearn: "नागरिक दिशानिर्देश देखें",

    // Portal Cards
    portalSelectorTitle: "विभागीय पोर्टल चुनें",
    portalSelectorSubtitle: "जांच अधिकारियों, न्यायिक पीठों, फॉरेंसिक प्रयोगशालाओं एवं नागरिकों हेतु समर्पित प्रवेश द्वार।",
    
    cardPoliceTitle: "पुलिस / जांच अधिकारी",
    cardPoliceDesc: "औपचारिक प्राथमिकी (FIR) दर्ज करें, साक्ष्य अपलोड करें, पूरक प्रतिवेदन हेतु अनुरोध करें और अभिरक्षा श्रृंखला देखें।",
    cardPoliceBtn: "पुलिस पोर्टल लॉगिन",

    cardJudicialTitle: "न्यायिक प्राधिकरण",
    cardJudicialDesc: "न्यायालय में प्रस्तुत साक्ष्यों की गणितीय सत्यता जांचें और अनुमोदन कतारों पर निर्णय लें।",
    cardJudicialBtn: "न्यायिक पोर्टल लॉगिन",

    cardForensicTitle: "फॉरेंसिक विशेषज्ञ",
    cardForensicDesc: "प्रयोगशाला परीक्षण रिपोर्ट अपलोड करें, साक्ष्य संवेदनशीलता का विश्लेषण करें और भौतिक नमूनों की सुरक्षा दर्ज करें।",
    cardForensicBtn: "फॉरेंसिक लैब लॉगिन",

    cardCitizenTitle: "नागरिक — अभिलेख स्थिति जानें",
    cardCitizenDesc: "अपनी दर्ज प्राथमिकी या शिकायत की अद्यतन स्थिति जानें। ओटीपी सत्यापन के साथ सरल भाषा में स्पष्ट जानकारी।",
    cardCitizenBtn: "स्थिति देखें",

    // Citizen Portal
    citizenLoginTitle: "नागरिक अभिलेख पोर्टल",
    citizenLoginSubtitle: "अपनी दर्ज प्राथमिकी या आधिकारिक शिकायत की जांच स्थिति देखें।",
    tabMobileNumber: "मोबाइल नंबर द्वारा",
    tabAckNumber: "पावती / प्राथमिकी संख्या द्वारा",
    mobileNumberLabel: "पंजीकृत मोबाइल नंबर",
    mobilePlaceholder: "10 अंकों का मोबाइल नंबर दर्ज करें",
    ackNumberLabel: "पावती / शिकायत संख्या",
    ackPlaceholder: "उदा. ACK-2024-88412 अथवा FIR-2024-ND-0842",
    sendOtpBtn: "सत्यापन कोड भेजें",
    verifyAndLoginBtn: "सत्यापित करें व स्थिति देखें",
    demoCitizenNotice: "डेमो: मोबाइल 9876543210 अथवा पावती ACK-2024-88412, ओटीपी: 123456",
    autoLogoutWarning: "सत्र समाप्ति समय शेष:",
    autoLogoutNotice: "सुरक्षा कारणों से, 10 मिनट निष्क्रिय रहने पर नागरिक सत्र स्वतः समाप्त हो जाता है।",
    myRecordsHeading: "मेरी पंजीकृत शिकायतें एवं प्राथमिकी",
    myRecordsSubheading: "गृह मंत्रालय द्वारा सत्यापित आधिकारिक अभिलेख स्थिति",
    noRecordsFound: "आपके विवरण से जुड़ा कोई प्रकरण नहीं मिला।",
    dateFiled: "पंजीकरण तिथि",
    currentStatus: "वर्तमान स्थिति",
    stationFiled: "संबंधित थाना",
    viewDetails: "विवरण देखें",

    // Plain Language Status (Citizen Facing)
    statusUnderInvestigation: "जांच जारी है",
    statusUpdatePending: "समीक्षा लंबित है",
    statusApprovedLocked: "प्रमाणित व सुरक्षित",
    statusClosed: "प्रकरण बंद",

    // Dashboards Common
    dashboardHeading: "प्रकरण डैशबोर्ड",
    dashboardSubheading: "राष्ट्रीय जांच दस्तावेज़ लेजर • पूर्णतः प्रमाणित अभिरक्षा",
    newDocumentBtn: "+ नया दस्तावेज़ जोड़ें",
    searchPlaceholder: "प्राथमिकी सं., शीर्षक, थाना या अभियुक्त द्वारा खोजें...",
    statusFilterLabel: "स्थिति",
    filterAll: "सभी अभिलेख",
    filterLocked: "सुरक्षित (आधिकारिक)",
    filterPending: "अनुमोदन लंबित",
    filterRejected: "अस्वीकृत",
    showingCount: "प्रदर्शित अभिलेख",

    // Police Dashboard Widgets
    policeWidgetActiveCases: "मेरे सक्रिय प्रकरण",
    policeWidgetPendingEdits: "मेरे लंबित संशोधन अनुरोध",
    policeWidgetCustodyTracker: "साक्ष्य अभिरक्षा श्रृंखला",
    policeWidgetCustodyDesc: "लेजर में दर्ज कालक्रमानुसार साक्ष्य हस्तांतरण:",
    policeNotificationTitle: "सक्रिय कोरम अधिसूचना",
    policeNotificationBody: "प्राथमिकी {firNo} पर आपके पूरक संशोधन हेतु पर्यवेक्षी अनुमोदन आवश्यक है।",

    // Judicial Dashboard Widgets
    judicialWidgetPendingVerify: "न्यायिक सत्यापन हेतु प्रस्तुत प्रकरण",
    judicialWidgetHashTool: "साक्ष्य सत्यता सत्यापन उपकरण",
    judicialWidgetHashDesc: "न्यायालय में प्रस्तुत साक्ष्य की मूल लेजर सील से सत्यता की तत्काल पुष्टि करें।",
    judicialWidgetDeAnon: "पहचान प्रकटीकरण अनुरोध (ऑडिट प्राधिकारी)",
    judicialWidgetDeAnonDesc: "समीक्षक की पहचान का कानूनी प्रकटीकरण। लिखित न्यायिक औचित्य अनिवार्य है और यह ऑडिट लॉग में दर्ज होता है।",
    judicialWidgetQueue: "न्यायिक अनुमोदन कतार",
    verifyHashBtn: "सत्यता की पुष्टि करें",
    simulateTamperBtn: "अवैध परिवर्तन का परीक्षण करें",
    matchSuccess: "सत्यापित — अपरिवर्तित: साक्ष्य मूल रिकॉर्ड से शत-प्रतिशत मेल खाता है। कोई छेड़छाड़ नहीं हुई।",
    mismatchError: "विसंगति — सत्यता उल्लंघन: दस्तावेज़ की सामग्री सुरक्षित लेजर सील से मेल नहीं खाती!",

    // Forensic Dashboard Widgets
    forensicWidgetAwaiting: "सील हेतु प्रतीक्षारत रिपोर्ट",
    forensicWidgetOcrQueue: "ओसीआर व पाठ्य विश्लेषण कतार",
    forensicWidgetSampleCustody: "भौतिक व डिजिटल नमूनों की अभिरक्षा",
    forensicWidgetPendingQuorum: "मेरी लंबित कोरम समीक्षाएं",
    confirmAndSealBtn: "पुष्टि करें व सील लगाएं",

    // Quorum Screen
    quorumHeading: "अनुमोदन स्थिति",
    quorumSubheading: "स्वतंत्र बहु-अधिकारी समीक्षा कतार",
    quorumThresholdLabel: "अनुमोदन प्राप्त हुए",
    quorumRequesterBlocked: "अनुरोधकर्ता स्वयं के अनुरोध को अनुमोदित नहीं कर सकता (सर्वर द्वारा वर्जित)",
    castVoteApprove: "संशोधन स्वीकृत करें",
    castVoteReject: "संशोधन अस्वीकार करें",
    commentsLabel: "पर्यवेक्षी समीक्षा टिप्पणी",
    consensusAchieved: "कोरम सीमा पूर्ण हुई। अभिलेख स्थायी रूप से अद्यतन किया गया।",

    // WORM Audit Log
    auditHeading: "WORM ऑडिट लॉग",
    auditSubheading: "राइट-वन्स रीड-मेनी अभिलेख इतिहास। अद्यतन अथवा विलोपन पूर्णतः प्रतिबंधित है।",
    auditAppendOnlyNotice: "अपरिवर्तनीय नियम: सभी प्रविष्टियां कालक्रमानुसार स्थायी रूप से दर्ज की जाती हैं।",
    auditVerifyAllBtn: "लेजर सत्यता जांचें",
    auditSimulateTamper: "छेड़छाड़ का अनुकरण करें",
    auditResetBtn: "लेजर रीसेट करें",

    // Status Badges
    badgeLocked: "सुरक्षित",
    badgePendingQuorum: "कोरम लंबित",
    badgeRejected: "अस्वीकृत",
    badgeApproved: "अनुमोदित",

    // Footer
    footerManagedBy: "वेबसाइट सामग्री गृह मंत्रालय, भारत सरकार द्वारा प्रबंधित।",
    footerHostedBy: "राष्ट्रीय सूचना विज्ञान केंद्र (एनआईसी) द्वारा होस्ट किया गया।",
    footerPolicyPrivacy: "गोपनीयता नीति",
    footerPolicyTerms: "अभिलेख अभिरक्षा की शर्तें",
    footerPolicyHyperlink: "हाइपरलिंकिंग नीति",
    footerPolicyCopyright: "कॉपीराइट वक्तव्य",
    footerPolicyAccessibility: "अभिगम्यता वक्तव्य"
  }
};
