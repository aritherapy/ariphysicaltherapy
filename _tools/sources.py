"""Key sources shown at the bottom of condition guides ("Sources" list + schema.org citation).

    python3 _tools/sources.py                 # apply to every page listed in SOURCES (idempotent)
    python3 _tools/sources.py sciatica-back-pain knee-pain-arthritis

build_condition.py also applies these on every build, so a rebuilt page keeps its sources.
Only use pages that were opened and checked (title matches the topic). Prefer, in order: APTA/JOSPT clinical
practice guidelines, other specialty-society guidelines, then NIH (MedlinePlus, NIAMS, NIDDK, NIDCR, NIA), CDC,
AAOS OrthoInfo, ACOG, womenshealth.gov and HealthyChildren.org (AAP) patient pages. 2-4 per page. Links checked 2026-10-11
(journal DOIs via Crossref, PubMed IDs via NCBI E-utilities, everything else opened directly).
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOSPT = 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)'
SOURCES = {
    'sciatica-back-pain': [
        ('Interventions for the Management of Acute and Chronic Low Back Pain: Revision 2021', JOSPT, '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0304'),
        ('Sciatica', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/000686.htm'),
        ('Back Pain', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIH)', '', 'https://www.niams.nih.gov/health-topics/back-pain'),
    ],
    'knee-pain-arthritis': [
        ('2019 American College of Rheumatology/Arthritis Foundation Guideline for the Management of Osteoarthritis of the Hand, Hip, and Knee', 'Arthritis &amp; Rheumatology', '2020', 'https://doi.org/10.1002/art.41142'),
        ('Arthritis of the Knee', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/arthritis-of-the-knee/'),
        ('Osteoarthritis', 'Centers for Disease Control and Prevention', '', 'https://www.cdc.gov/arthritis/osteoarthritis/index.html'),
    ],
    'frozen-shoulder-rotator-cuff': [
        ('Shoulder Pain and Mobility Deficits: Adhesive Capsulitis', JOSPT, '2013', 'https://www.jospt.org/doi/10.2519/jospt.2013.0302'),
        ('Frozen Shoulder', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/frozen-shoulder/'),
        ('Rotator Cuff Tears', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/rotator-cuff-tears/'),
    ],
    'bladder-leaks-incontinence': [
        ('Urinary Incontinence', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/urinary-incontinence'),
        ('Bladder Control Problems (Urinary Incontinence)', 'National Institute of Diabetes and Digestive and Kidney Diseases (NIH)', '', 'https://www.niddk.nih.gov/health-information/urologic-diseases/bladder-control-problems'),
        ('Urinary Incontinence', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/urinaryincontinence.html'),
    ],
    'car-accident-whiplash': [
        ('Neck Pain: Revision 2017', JOSPT, '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Neck Sprains and Strains', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/neck-sprain/'),
        ('Neck Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/neckinjuriesanddisorders.html'),
    ],
    'tennis-elbow-golfers-elbow': [
        ('Lateral Elbow Pain and Muscle Function Impairments', JOSPT, '2022', 'https://www.jospt.org/doi/10.2519/jospt.2022.0302'),
        ('Tennis Elbow (Lateral Epicondylitis)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/tennis-elbow-lateral-epicondylitis/'),
        ('Tennis elbow', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/000449.htm'),
    ],
    'tmj-jaw-pain': [
        ('TMD (Temporomandibular Disorders)', 'National Institute of Dental and Craniofacial Research (NIH)', '', 'https://www.nidcr.nih.gov/health-info/tmd'),
        ('Temporomandibular Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/temporomandibulardisorders.html'),
    ],
    'balance-fall-prevention': [
        ('Older Adult Fall Prevention', 'Centers for Disease Control and Prevention', '', 'https://www.cdc.gov/falls/about/index.html'),
        ('Falls and Fractures in Older Adults: Causes and Prevention', 'National Institute on Aging (NIH)', '', 'https://www.nia.nih.gov/health/falls-and-falls-prevention/falls-and-fractures-older-adults-causes-and-prevention'),
        ('Falls', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/falls.html'),
    ],
    'pelvic-organ-prolapse': [
        ('Pelvic Support Problems', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/pelvic-support-problems'),
        ('Pelvic Organ Prolapse', 'Office on Women&rsquo;s Health, U.S. Department of Health and Human Services', '', 'https://womenshealth.gov/a-z-topics/pelvic-organ-prolapse'),
        ('Pelvic Support Problems', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/pelvicfloordisorders.html'),
    ],
    'pelvic-pain-painful-sex': [
        ('Chronic Pelvic Pain', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/chronic-pelvic-pain'),
        ('When Sex Is Painful', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/when-sex-is-painful'),
        ('Pelvic Pain', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/pelvicpain.html'),
    ],
    'vertigo-dizziness-bppv': [
        ('Clinical Practice Guideline: Benign Paroxysmal Positional Vertigo (Update)', 'Otolaryngology&ndash;Head and Neck Surgery (American Academy of Otolaryngology&ndash;Head and Neck Surgery Foundation clinical practice guideline)', '2017', 'https://doi.org/10.1177/0194599816689667'),
        ('Benign positional vertigo', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/001420.htm'),
        ('Balance Disorders', 'National Institute on Deafness and Other Communication Disorders (NIDCD), NIH', '', 'https://www.nidcd.nih.gov/health/balance-disorders'),
    ],
    'plantar-fasciitis-heel-pain': [
        ('Heel Pain &ndash; Plantar Fasciitis: Revision 2023', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2023', 'https://www.jospt.org/doi/10.2519/jospt.2023.0303'),
        ('Plantar Fasciitis and Bone Spurs', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/plantar-fasciitis-and-bone-spurs/'),
        ('Plantar fasciitis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/007021.htm'),
    ],
    'diastasis-recti': [
        ('Diastasis recti', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/001602.htm'),
        ('Exercise After Pregnancy', 'American College of Obstetricians and Gynecologists (ACOG)', '', 'https://www.acog.org/womens-health/faqs/exercise-after-pregnancy'),
    ],
    'carpal-tunnel-hand-numbness': [
        ('Hand Pain and Sensory Deficits: Carpal Tunnel Syndrome', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2019', 'https://www.jospt.org/doi/10.2519/jospt.2019.0301'),
        ('Carpal Tunnel Syndrome', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/carpal-tunnel-syndrome/'),
        ('Carpal Tunnel Syndrome', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/carpaltunnelsyndrome.html'),
    ],
    'neck-pain-headaches': [
        ('Neck Pain: Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Neck Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/neckinjuriesanddisorders.html'),
        ('Tension headache', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/000797.htm'),
    ],
    'osteoporosis-bone-health': [
        ('Physical Therapist Management of Patients With Suspected or Confirmed Osteoporosis: A Clinical Practice Guideline From the Academy of Geriatric Physical Therapy', 'Journal of Geriatric Physical Therapy (APTA Geriatrics clinical practice guideline)', '2022', 'https://doi.org/10.1519/JPT.0000000000000346'),
        ('Osteoporosis', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS), NIH', '', 'https://www.niams.nih.gov/health-topics/osteoporosis'),
        ('Exercise/Safe Movement', 'Bone Health &amp; Osteoporosis Foundation', '', 'https://www.bonehealthandosteoporosis.org/patients/treatment/exercisesafe-movement/'),
    ],
    'prehab-before-surgery': [
        ('Physical Therapist Management of Total Knee Arthroplasty', 'Physical Therapy journal (APTA clinical practice guideline)', '2020', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7462050/'),
        ('Preparing for Joint Replacement Surgery', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/preparing-for-joint-replacement-surgery/'),
        ('Getting your home ready &ndash; knee or hip surgery', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/patientinstructions/000167.htm'),
    ],
    'hip-pain': [
        ('Hip Pain and Mobility Deficits&mdash;Hip Osteoarthritis: Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0301'),
        ('Hip Osteoarthritis', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/osteoarthritis-of-the-hip/'),
        ('Hip pain', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/003179.htm'),
    ],
    'knee-hip-replacement-rehab': [
        ('Physical Therapist Management of Total Knee Arthroplasty', 'Physical Therapy journal (APTA clinical practice guideline)', '2020', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7462050/'),
        ('Total Knee Replacement', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/total-knee-replacement/'),
        ('Total Hip Replacement', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/total-hip-replacement/'),
    ],
    'pregnancy-back-pelvic-pain': [
        ('Pelvic Girdle Pain in the Antepartum Population: Physical Therapy Clinical Practice Guidelines', 'Journal of Women&rsquo;s Health Physical Therapy (APTA clinical practice guideline)', '2017', 'https://doi.org/10.1097/JWH.0000000000000081'),
        ('Back Pain During Pregnancy', 'American College of Obstetricians and Gynecologists (ACOG)', '', 'https://www.acog.org/womens-health/faqs/back-pain-during-pregnancy'),
        ('Exercise During Pregnancy', 'American College of Obstetricians and Gynecologists (ACOG)', '', 'https://www.acog.org/womens-health/faqs/exercise-during-pregnancy'),
    ],
    'ankle-sprain-achilles-pain': [
        ('Ankle Stability and Movement Coordination Impairments: Lateral Ankle Ligament Sprains Revision 2021', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0302'),
        ('Achilles Pain, Stiffness, and Muscle Power Deficits: Midportion Achilles Tendinopathy Revision 2018', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2018', 'https://www.jospt.org/doi/10.2519/jospt.2018.0302'),
        ('Sprained Ankle', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/sprained-ankle/'),
    ],
    'acl-mcl-knee-ligament-injuries': [
        ('Knee Stability and Movement Coordination Impairments: Knee Ligament Sprain Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0303'),
        ('Anterior Cruciate Ligament (ACL) Injuries', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/anterior-cruciate-ligament-acl-injuries/'),
        ('Collateral Ligament Injuries', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/collateral-ligament-injuries/'),
    ],
    'shoulder-surgery-rehab': [
        ('The American Society of Shoulder and Elbow Therapists&rsquo; consensus statement on rehabilitation following arthroscopic rotator cuff repair', 'Journal of Shoulder and Elbow Surgery (consensus statement), via PubMed', '2016', 'https://pubmed.ncbi.nlm.nih.gov/26995456/'),
        ('Rotator Cuff Tears: Surgical Treatment Options', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/rotator-cuff-tears-surgical-treatment-options/'),
        ('Shoulder Joint Replacement', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/shoulder-joint-replacement/'),
    ],
    'spine-surgery-rehab': [
        ('Rehabilitation after lumbar disc surgery', 'Cochrane Database of Systematic Reviews, via PubMed', '2014', 'https://pubmed.ncbi.nlm.nih.gov/24627325/'),
        ('Diskectomy', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/007250.htm'),
        ('Spinal Fusion', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/treatment/spinal-fusion/'),
    ],
    'fracture-recovery': [
        ('Physical Therapy Management of Older Adults With Hip Fracture', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0301'),
        ('Fractures (Broken Bones)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/fractures-broken-bones/'),
        ('Fractures', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/fractures.html'),
    ],
    'muscle-strains': [
        ('Hamstring Strain Injury in Athletes', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2022', 'https://www.jospt.org/doi/10.2519/jospt.2022.0301'),
        ('Sprains and Strains', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/sprainsandstrains.html'),
        ('Muscle Strains in the Thigh', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/muscle-strains-in-the-thigh/'),
    ],
    'tendonitis-overuse-injuries': [
        ('Lateral Elbow Pain and Muscle Function Impairments', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2022', 'https://www.jospt.org/doi/10.2519/jospt.2022.0302'),
        ('Tendinitis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/tendinitis.html'),
        ('Achilles Tendinitis', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/achilles-tendinitis/'),
    ],
    'fibromyalgia': [
        ('EULAR revised recommendations for the management of fibromyalgia', 'Annals of the Rheumatic Diseases (EULAR recommendations), via PubMed', '2017', 'https://pubmed.ncbi.nlm.nih.gov/27377815/'),
        ('Fibromyalgia', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS)', '', 'https://www.niams.nih.gov/health-topics/fibromyalgia'),
        ('Fibromyalgia', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/fibromyalgia.html'),
    ],
    'c-section-recovery': [
        ('Physical Activity and Exercise During Pregnancy and the Postpartum Period', 'American College of Obstetricians and Gynecologists (committee opinion)', '2020', 'https://www.acog.org/clinical/clinical-guidance/committee-opinion/articles/2020/04/physical-activity-and-exercise-during-pregnancy-and-the-postpartum-period'),
        ('Cesarean Birth', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/cesarean-birth'),
        ('Cesarean Section', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/cesareandelivery.html'),
    ],
    'bowel-leakage': [
        ('Fecal Incontinence', 'American College of Obstetricians and Gynecologists (practice bulletin)', '2019', 'https://www.acog.org/clinical/clinical-guidance/practice-bulletin/articles/2019/04/fecal-incontinence'),
        ('Accidental Bowel Leakage', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/accidental-bowel-leakage'),
        ('Bowel Control Problems (Fecal Incontinence)', 'National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)', '', 'https://www.niddk.nih.gov/health-information/digestive-diseases/bowel-control-problems-fecal-incontinence'),
    ],
    'interstitial-cystitis-bladder-pain': [
        ('Diagnosis and Treatment of Interstitial Cystitis/Bladder Pain Syndrome (2022)', 'American Urological Association (AUA clinical guideline)', '2022', 'https://www.auanet.org/guidelines-and-quality/guidelines/diagnosis-and-treatment-interstitial-of-cystitis/bladder-pain-syndrome-(2022)'),
        ('Interstitial Cystitis (Bladder Pain Syndrome)', 'National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)', '', 'https://www.niddk.nih.gov/health-information/urologic-diseases/interstitial-cystitis-bladder-pain-syndrome'),
        ('Interstitial Cystitis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/interstitialcystitis.html'),
    ],
    'hand-wrist-therapy': [
        ('Hand Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/handinjuriesanddisorders.html'),
        ('Wrist Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/wristinjuriesanddisorders.html'),
        ('De Quervain&rsquo;s Tenosynovitis', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/de-quervains-tendinosis/'),
    ],
    'running-injuries-running-assessment': [
        ('Patellofemoral Pain', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2019', 'https://www.jospt.org/doi/10.2519/jospt.2019.0302'),
        ('Shin Splints', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/shin-splints/'),
        ('Stress Fractures', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/stress-fractures/'),
    ],
    'youth-sports-injuries': [
        ('Overuse Injuries, Overtraining, and Burnout in Young Athletes', 'Pediatrics, American Academy of Pediatrics (clinical report)', '2024', 'https://publications.aap.org/pediatrics/article/153/2/e2023065129/196435/Overuse-Injuries-Overtraining-and-Burnout-in-Young'),
        ('Sports Injuries', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/health-issues/injuries-emergencies/sports-injuries/Pages/default.aspx'),
        ('Osgood-Schlatter Disease (Knee Pain)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/osgood-schlatter-disease-knee-pain/'),
    ],
    'herniated-disc-bulging-disc': [
        ('Interventions for the Management of Acute and Chronic Low Back Pain: Revision 2021', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0304'),
        ('Herniated Disk', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/herniateddisk.html'),
        ('Herniated Disk in the Lower Back', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/herniated-disk-in-the-lower-back/'),
    ],
    'pinched-nerve-neck': [
        ('Neck Pain: Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Cervical Radiculopathy (Pinched Nerve)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/cervical-radiculopathy-pinched-nerve/'),
        ('Neck Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/neckinjuriesanddisorders.html'),
    ],
    'spinal-stenosis': [
        ('Spinal Stenosis', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS)', '', 'https://www.niams.nih.gov/health-topics/spinal-stenosis'),
        ('Lumbar Spinal Stenosis', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/lumbar-spinal-stenosis/'),
        ('Spinal Stenosis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/spinalstenosis.html'),
    ],
    'si-joint-pain': [
        ('Interventions for the Management of Acute and Chronic Low Back Pain: Revision 2021', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0304'),
        ('Back Pain', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS)', '', 'https://www.niams.nih.gov/health-topics/back-pain'),
        ('Back Pain', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/backpain.html'),
    ],
    'shoulder-impingement-bursitis': [
        ('Rotator Cuff Tendinopathy Diagnosis, Nonsurgical Medical Care, and Rehabilitation: A Clinical Practice Guideline', 'Journal of Orthopaedic &amp; Sports Physical Therapy (clinical practice guideline)', '2025', 'https://www.jospt.org/doi/10.2519/jospt.2025.13182'),
        ('Shoulder Impingement/Rotator Cuff Tendinitis', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/shoulder-impingementrotator-cuff-tendinitis/'),
        ('Bursitis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/bursitis.html'),
    ],
    'meniscus-tear': [
        ('Knee Pain and Mobility Impairments: Meniscal and Articular Cartilage Lesions Revision 2018', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2018', 'https://www.jospt.org/doi/10.2519/jospt.2018.0301'),
        ('Meniscus Tears', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/meniscus-tears/'),
        ('Knee Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/kneeinjuriesanddisorders.html'),
    ],
    'osteoarthritis-joint-pain': [
        ('2019 American College of Rheumatology/Arthritis Foundation Guideline for the Management of Osteoarthritis of the Hand, Hip, and Knee', 'Arthritis Care &amp; Research (American College of Rheumatology / Arthritis Foundation guideline)', '2020', 'https://doi.org/10.1002/acr.24131'),
        ('Osteoarthritis', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS), NIH', '', 'https://www.niams.nih.gov/health-topics/osteoarthritis'),
        ('Osteoarthritis', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/osteoarthritis.html'),
    ],
    'upper-back-pain-posture': [
        ('Neck Pain: Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Back Pain', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS), NIH', '', 'https://www.niams.nih.gov/health-topics/back-pain'),
        ('Back Pain', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/backpain.html'),
    ],
    'torticollis-in-babies': [
        ('Physical Therapy Management of Congenital Muscular Torticollis: A 2024 Evidence-Based Clinical Practice Guideline From the American Physical Therapy Association Academy of Pediatric Physical Therapy', 'Pediatric Physical Therapy (APTA clinical practice guideline)', '2024', 'https://doi.org/10.1097/PEP.0000000000001114'),
        ('Head Tilt (Torticollis)', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/health-issues/conditions/Cleft-Craniofacial/Pages/Head-Tilt.aspx'),
        ('When a Baby&rsquo;s Head is Misshapen: Positional Skull Deformities', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/health-issues/conditions/Cleft-Craniofacial/Pages/Positional-Skull-Deformities-and-Torticollis.aspx'),
    ],
    'flat-head-plagiocephaly': [
        ('Congress of Neurological Surgeons Systematic Review and Evidence-Based Guidelines for the Management of Patients With Positional Plagiocephaly', 'Neurosurgery (Congress of Neurological Surgeons guideline)', '2016', 'https://doi.org/10.1227/NEU.0000000000001426'),
        ('When a Baby&rsquo;s Head is Misshapen: Positional Skull Deformities', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/health-issues/conditions/Cleft-Craniofacial/Pages/Positional-Skull-Deformities-and-Torticollis.aspx'),
        ('Baby Helmet Therapy: Parent FAQs', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/health-issues/conditions/Cleft-Craniofacial/Pages/Baby-Helmet-Therapy-Parent-FAQs.aspx'),
    ],
    'gross-motor-delays': [
        ('Motor Delays: Early Identification and Evaluation', 'Pediatrics (American Academy of Pediatrics clinical report)', '2013', 'https://publications.aap.org/pediatrics/article/131/6/e2016/31072/Motor-Delays-Early-Identification-and-Evaluation'),
        ('CDC&rsquo;s Developmental Milestones', 'Centers for Disease Control and Prevention', '', 'https://www.cdc.gov/act-early/milestones/index.html'),
        ('Is Your Baby&rsquo;s Physical Development on Track?', 'HealthyChildren.org, American Academy of Pediatrics', '', 'https://www.healthychildren.org/English/ages-stages/baby/Pages/Is-Your-Babys-Physical-Development-on-Track.aspx'),
    ],
    'coordination-problems-in-kids': [
        ('International clinical practice recommendations on the definition, diagnosis, assessment, intervention, and psychosocial aspects of developmental coordination disorder', 'Developmental Medicine &amp; Child Neurology (European Academy of Childhood Disability recommendations)', '2019', 'https://doi.org/10.1111/dmcn.14132'),
        ('Developmental coordination disorder', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/001533.htm'),
        ('Developmental Coordination Disorder', 'CanChild, McMaster University', '', 'https://canchild.ca/diagnoses/developmental-coordination-disorder/'),
    ],
    'toe-walking-in-kids': [
        ('The management of idiopathic toe walking', 'The Bone &amp; Joint Journal (consensus statement)', '2024', 'https://boneandjoint.org.uk/article/10.1302/0301-620X.106B10.BJJ-2024-0466.R1'),
        ('Toe Walking', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/toe-walking/'),
    ],
    'headaches-migraines': [
        ('Neck Pain: Revision 2017', 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)', '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Headache', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/headache.html'),
        ('Migraine', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/migraine.html'),
    ],
    'tailbone-pain-coccyx': [
        ('Tailbone Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/tailbonedisorders.html'),
        ('Tailbone trauma &ndash; aftercare', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/patientinstructions/000573.htm'),
        ('Coccyx Pain', 'StatPearls, NCBI Bookshelf, National Library of Medicine', '', 'https://www.ncbi.nlm.nih.gov/books/NBK563139/'),
    ],
    'foot-ankle-surgery-rehab': [
        ('Ankle Fractures (Broken Ankle)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/ankle-fractures-broken-ankle/'),
        ('Achilles Tendon Rupture (Tear)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/achilles-tendon-rupture-tear/'),
        ('Foot and Ankle Conditioning Program', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/recovery/foot-and-ankle-conditioning-program/'),
    ],
}

START, END = '<!-- sources -->', '<!-- /sources -->'


def block(slug):
    items = ''.join(f'<li><a href="{u}" rel="noopener" target="_blank">{t}</a>. {p}{", " + y if y else ""}.</li>'
                    for t, p, y, u in SOURCES[slug])
    return f'{START}<div class="sources"><h2>Sources</h2><ol>{items}</ol></div>{END}'


def citations(slug):
    out = []
    for t, p, y, u in SOURCES[slug]:
        c = {'@type': 'CreativeWork', 'name': html.unescape(t), 'url': u, 'publisher': {'@type': 'Organization', 'name': html.unescape(p.split(' (APTA')[0])}}
        if y: c['datePublished'] = y
        out.append(c)
    return out


def apply(slug, s):
    """Return page HTML with the Sources block (before the disclaimer) and schema citations set."""
    if slug not in SOURCES:
        return s
    s = re.sub(re.escape(START) + '.*?' + re.escape(END), '', s, flags=re.S)
    assert s.count('<p class="med-disclaimer">') == 1, slug
    s = s.replace('<p class="med-disclaimer">', block(slug) + '<p class="med-disclaimer">', 1)
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        if '"MedicalWebPage"' in b:
            d = json.loads(b)
            d['citation'] = citations(slug)
            s = s.replace(b, '\n' + json.dumps(d, indent=2, ensure_ascii=False) + '\n    ', 1)
    return s


if __name__ == '__main__':
    for slug in sys.argv[1:] or sorted(SOURCES):
        f = os.path.join(ROOT, slug + '.html')
        s = open(f, encoding='utf-8').read()
        open(f, 'w', encoding='utf-8').write(apply(slug, s))
        print(slug, len(SOURCES[slug]), 'sources')
