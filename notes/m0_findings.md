# M0 findings

Status: in progress. Every value below comes from running the step on the real file.

## 0.4 Ascension links (read from the live page, 2026-11-05)

- West: https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1629025648_saint-thomas-west-hospital_standardcharges.csv
- Rutherford: https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620475842_saint-thomas-rutherford-hospital_standardcharges.csv
- Midtown (separate link, file name says saint-thomas-west): https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1780778969_saint-thomas-west-hospital_standardcharges.csv

West and Rutherford match PROJECT_CONTEXT B3.

## 0.7 Midtown

Midtown is not a location in the West file. West lists only `Ascension Saint Thomas West`. Midtown has its own file (the third link above), which lists `Ascension Saint Thomas Midtown`, but its `hospital_name` still says Saint Thomas West and it carries the same type 2 NPI (1629025648). It validates clean and has all 10 codes. Status: added as source 12 on 2026-11-05, Chaz approved. It is not a copy of West: 72 MB against West's much larger file, and the MRI code 70553 has a median of $342.02 against West's $490.91.

## 0.5, 0.6, 0.8 Per-file facts

| file | MB | layout | columns | items or rows | version | file date | type_2_npi | attester | valid | errors | alerts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vumc_main | 203 | tall | 29 | 733,800 | 3.0.0 | 2026-10-01 | yes | yes | True | 0 | 0 |
| vumc_clarksville | 213 | json | n/a | 9,636 | 3.0.0 | 2026-01-01 | yes | yes | True | 0 | 0 |
| tristar_centennial | 593 | json | n/a | 342,788 | 3.0.0 | 2026-09-01 | yes | yes | True | 0 | 0 |
| ascension_west | 337 | tall | 24 | 1,401,798 | 3.0.0 | 01/01/2026 | yes | yes | True | 0 | 0 |
| ascension_midtown | 72 | tall | 24 | 299,398 | 3.0.0 | 01/01/2026 | yes | yes | True | 0 | 0 |

The validator reported no errors, so there are no common error messages to list for any file.

## 0.9 Raw code matches (rows, by code and code type)

- **vumc_main:** 29881 CDM (1), 29881 CPT (174), 29881 HCPCS (31), 43235 CDM (1), 43235 CPT (547), 43235 HCPCS (31), 45378 CDM (1), 45378 CPT (872), 45378 HCPCS (31), 470 MS-DRG (142), 66984 CDM (1), 66984 CPT (443), 66984 HCPCS (31), 70553 CDM (3), 70553 CPT (662), 70553 HCPCS (19), 70553 LOCAL (1), 74177 CDM (3), 74177 CPT (564), 74177 HCPCS (19), 76700 CDM (4), 76700 CPT (266), 76700 HCPCS (19), 77067 CDM (3), 77067 CPT (304), 77067 HCPCS (15), 80053 HCPCS (25)
- **vumc_clarksville:** 29881 CPT (2), 43235 CPT (2), 45378 CPT (2), 470 MS-DRG (1), 70553 CPT (2), 74177 CPT (6), 76700 CPT (4), 77067 CPT (2), 80053 CPT (2)
- **tristar_centennial:** 29881 CPT (11), 43235 CPT (13), 45378 CPT (13), 470 MS-DRG (19), 470 RC (548), 470 TRIS-DRG (1), 66984 CPT (13), 70553 CPT (13), 74177 CPT (13), 76700 CPT (8), 77067 CPT (9), 80053 CPT (19)
- **ascension_west:** 29881 CPT (7), 43235 CPT (68), 45378 CPT (68), 470 MS-DRG (79), 470 RC (12), 66984 CPT (7), 70553 CPT (209), 74177 CPT (94), 76700 CPT (93), 77067 CPT (214), 80053 CPT (126)
- **ascension_midtown:** 29881 CPT (4), 43235 CPT (47), 45378 CPT (47), 470 MS-DRG (44), 470 RC (2), 66984 CPT (4), 70553 CPT (57), 74177 CPT (57), 76700 CPT (57), 77067 CPT (60), 80053 CPT (60)

## 0.10 Payer names (up to 50 per file)

- **vumc_main (36 total):** `Accarent`; `Aetna`; `Alliant Health Plans`; `Ambetter`; `Ambetter Health`; `BCBS`; `Center Care`; `Cigna`; `Deaconess Hospital Inc`; `Delta Dental`; `DentaQuest`; `Direct to Employer`; `Health One Alliance`; `HealthSpring`; `HeathSpring`; `Humana`; `INTERLINK`; `Interlink`; `LifeTrac`; `Magellan Health`; `MetLife`; `Molina`; `Molina Healthcare`; `NAMCI`; `NovaNet`; `Optum`; `Oscar`; `PHCS`; `Prime Health Services`; `UMR`; `UnitedHealthCare`; `UnitedHealthcare`; `VA CCN`; `WellCare`; `Wellcare`; `Wellpoint`
- **vumc_clarksville (53 total):** `Aetna`; `Aetna Better Health MCD KY`; `Ambetter`; `Ambetter HIX`; `American Health`; `Amerigroup`; `BCBS TN`; `CHS Group Health Plan BCBST`; `Center Care`; `Cigna`; `Correct Care Solutions`; `Corvel`; `First Health`; `Humana`; `KY Work Comp`; `Medicaid KY`; `Multiplan`; `NODE Aetna MCR ADV`; `NODE Amerigroup MCR ADV`; `NODE Ascension Complete MCR ADV`; `NODE BlueCare Plus TN MCR ADV`; `NODE ChampVA`; `NODE Devoted Health MCR ADV`; `NODE Farm Bureau MCR ADV`; `NODE Healthspring MCR ADV`; `NODE Hospice Non Par Agree`; `NODE Medicare Non Par`; `NODE Medicare Traditional`; `NODE NHC MCR ADV`; `NODE Tricare`; `NODE UHC MCR ADV`; `NODE US Dept of Labor`; `NODE United Optum VA CCN`; `NODE VA`; `NODE Valenz Access`; `NODE Wellcare MCR ADV`; `NODE Windsor MCR Dual`; `NaphCare`; `NovaNet Work Comp TN`; `Oscar`; `PHCS`; `Prime Health Services`; `Prime Health Work Comp TN`; `Rockport Work Comp TN`; `Self Pay`; `TN Medicaid Non-Par`; `TN Work Comp`; `Tennessee Breast and Cervical Screening Program`; `UHC`; `UHC APA`
- **tristar_centennial (49 total):** `ATRIO Golden Times`; `Aetna`; `Alive Hospice, Inc.`; `Ambetter`; `American Health Advantage`; `Amerigroup`; `Apex Health`; `BCBS`; `BGFH SingleSource`; `Beech Street`; `Bright Health`; `Centurion`; `Cigna`; `Cigna Evernorth Behavioral Health`; `Cigna LifeSource`; `ComPsych`; `CorVel Corporation`; `Devoted Health Plan`; `Emerging Therapy Solutions`; `Employers Health Network`; `Evergreen HMO`; `Healthspring`; `Humana`; `Humana National Transplant`; `Kentucky Labor Cabinet`; `MHNet `; `Magellan Behavioral Health`; `Managed Healthcare Administration`; `Multiplan`; `NHC Advantage, Inc.`; `NovaNET`; `Odom's TN Pride Sausage`; `Odyssey Healthcare`; `OptumHealth`; `Oscar`; `Prime Health`; `Prime Health `; `Pruitt Health (AllyAlign)`; `Sarah Cannon Research`; `Signature Advantage`; `Southern Health Partners`; `Tennessee Donor Services`; `United`; `United Behavioral Health`; `UnitedHealthcare Plan of the River Valley`; `Value Option  `; `WellCare`; `Wellpoint`; `Zing`
- **ascension_west (46 total):** ` CDM DEFAULT - NON-NEGOTIATED RATE`; `AETNA`; `AETNA (RUTHERFORD ONLY)`; `AETNA MEDADVANTAGE`; `AMBETTER OF TN`; `AMERICHOICE MEDICARE`; `AMERIGROUP MCAID REPLACEMENT`; `AMERIGROUP MCR REPLACEMENT`; `ASCENSION COMPLETE`; `BCBS ACA EXCHANGE`; `BCBS BLUECARE PLUS`; `BCBS MCR REPLACEMENT`; `BCBS MISSIONPOINT`; `BCBS NETWORK E`; `BCBS NETWORK L`; `BCBS PREFERRED`; `BCBS SELECT`; `BCBS TENNCARE SELECT`; `CENTURION OF TN`; `CHRISTIAN HEALTHCARE MINISTRIES`; `CIGNA CONNECT`; `CIGNA HMO`; `CIGNA LOCALPLUS`; `CIGNA PPO`; `CIGNA SUREFIT`; `CLOVER MEDICARE ADVANTAGE`; `COMMUNITY PLAN`; `COVID UNINSURED TEST FUND`; `HEALTH 2 BUSINESS`; `HEALTHSPRING MCR REPLACEMENT`; `HUMANA +51 CPOS`; `HUMANA MCR REPLACEMENT`; `MEDICARE OTHER`; `MULTIPLAN`; `NHC ADVANTAGE`; `OPTUM VA`; `OSCAR HEALTH`; `PHCS`; `POINT COMFORT UNDERWRITERS`; `SELECT SPECIALTY WEST`; `SMART HEALTH`; `TRIWEST VA PCCC`; `UHC`; `UHC COMPASS/EXCHANGE`; `UHC MCR REPLACEMENT`; `WINDSOR MEDICARE`
- **ascension_midtown (44 total):** ` CDM DEFAULT - NON-NEGOTIATED RATE`; `AETNA`; `AETNA MEDADVANTAGE`; `AETNA VHAN`; `AETNA WHOLE HEALTH`; `AMBETTER OF TN`; `AMERICHOICE MCR REPLACEMENT`; `AMERIGROUP`; `AMERIGROUP MCR REPLACEMENT`; `ASCENSION COMPLETE MEDICARE ADVANTAGE`; `BCBS BLUCARE PLUS`; `BCBS BLUE CARE`; `BCBS MEDICARE REPLACEMENT`; `BCBS MISSIONPOINT`; `BCBS NETWORK E`; `BCBS NETWORK L`; `BCBS PREFERRED`; `BCBS SELECT`; `CENTURION OF TN`; `CIGNA CONNECT`; `CIGNA HMO`; `CIGNA LOCALPLUS`; `CIGNA PPO`; `CIGNA SUREFIT`; `CLOVER MEDICARE ADVANTAGE`; `COMMUNITY PLAN`; `COVID UNINSURED TEST FUND`; `HEALTHSPRING MCR REPLACEMENT`; `HUMANA +51 CPOS`; `HUMANA MCR REPLACEMENT`; `MD SAVE`; `MEDICARE OTHER`; `NHC ADVANTAGE`; `OPTUM VA`; `OSCAR HEALTH PLAN`; `PHCS`; `POINT COMFORT UNDERWRITERS`; `SMART HEALTH`; `TRICARE`; `TRIWEST VA PCCC`; `UHC`; `UHC COMPASS/EXCHANGE`; `UHC MCR REPLACEMENT`; `WINDSOR MEDICARE`

## Rate coverage for the 10 codes (added check, not in the checklist)

From `scratch/m0_rates.py`. CPT codes counted under types CPT and HCPCS, 470 under MS-DRG only. Almost every matched row has a dollar rate. Percentage and algorithm rates appear mainly on DRG 470 at vumc_main, vumc_clarksville, and tristar_centennial. Dollar rows per code range from 4 (Midtown 29881, 66984) to 903 (VUMC 45378).

## Findings that change the build

1. **Validator results are all clean.** 5 of 5 files are `valid: true` with 0 errors and 0 alerts. The tool is not a no-op: the CMS tall example passes, and a copy with a misspelled `description` header fails with 2 errors. The file quality page cannot lead on validator errors unless the other 6 files differ. File staleness is the stronger signal so far: Clarksville, West, and Midtown are dated January 1, 2026, about 10 months old on the download date, while VUMC is October 1, 2026 and Centennial is September 1, 2026. Whether those dates are out of compliance is `unverified`.
2. **Revenue code collision on 470.** `470 RC` appears in Centennial (548 rows), West (12), and Midtown (2). Those are revenue codes, not the DRG. Matching on the code alone would put wrong prices on the joint replacement row, and the 0.9 query in the checklist does not filter on type. `470 TRIS-DRG` also appears once in Centennial; it is a local grouper and is excluded.
3. **CPT codes are also labeled HCPCS.** VUMC labels 80053 only as HCPCS, so a CPT-only filter loses that procedure for its largest hospital. Staging must accept types CPT and HCPCS for the nine CPT codes. CDM and LOCAL rows are excluded.
4. **DRG coding.** Every file writes 470 as the literal `470` with type `MS-DRG`. No zero padding and no `DRG` label in these five files. Keep the normalization anyway for the other six.
5. **Missing code.** Clarksville has no 66984 under any type, so it is 9 of 10. The app must show this as not published, not as a gap in the pipeline.
6. **Payer cleanup is real work.** Spelling variants: `HealthSpring`/`HeathSpring`, `INTERLINK`/`Interlink`, `UnitedHealthCare`/`UnitedHealthcare`, `WellCare`/`Wellcare`, `Molina`/`Molina Healthcare`, `Ambetter`/`Ambetter Health` (VUMC); `UHC`/`United Healthcare` (Clarksville); `Prime Health`/`Prime Health ` plus trailing spaces on `MHNet ` and `Value Option  ` (Centennial); `BCBS BLUCARE PLUS` (Midtown) against `BCBS BLUECARE PLUS` (West). Not insurers, so they must not map as payers: ` CDM DEFAULT - NON-NEGOTIATED RATE` (Ascension, leading space), `Self Pay` (Clarksville). Ascension puts the product in the payer name, so its plan split differs from the other systems.
7. **Date formats differ.** Ascension uses `01/01/2026`, the others ISO. The spec allows this (B4), and silver must parse both.
8. **Attestation location differs.** JSON nests `attester_name` under `attestation`; CSV has it at the top level. The 0.6 snippet in the checklist reads the top level only, so it misses JSON.

## 0.11 Gate decision

- Any MVP file wide? No. All three CSVs are tall. The wide reader stays tested by fixture only, unless the other 6 files differ.
- Any file over 500 MB or a million rows? Yes. Centennial is 593 MB and West has 1,401,798 rows. Staging handled both, and all five files finished staging and validation in under 3 minutes.
- Are the 10 codes present in most files? Yes. 10 of 10 in four files, 9 of 10 in Clarksville.
- Is the scope still realistic? Yes.

**Decision: GO, no scope change.** Three adjustments go into the build: filter 470 by code type, accept HCPCS for CPT codes, and rethink the file quality page lead once all 11 files are validated. Not yet checked: the other 6 files, so "no wide files" and "all clean" hold only for these five.

## Real-file normalizer smoke test (added check, not in the checklist)

`scratch/m2_smoke_silver.py` ran the reference tall and JSON readers on the five staged files, locally, with no Iceberg or AWS. The 10-code rows and dollar counts match the independent counts in `scratch/m0_rates.py`.

| file | silver rows | 10-code rows | codes | dollar rows | min dollars | max dollars |
| --- | --- | --- | --- | --- | --- | --- |
| vumc_main | 897,184 | 4,195 | 10 | 4,110 | 0.01 | 68,033.03 |
| ascension_west | 2,416,290 | 965 | 10 | 965 | 9.50 | 48,919.84 |
| ascension_midtown | 299,398 | 437 | 10 | 437 | 3.80 | 56,673.86 |
| vumc_clarksville | 778,675 | 774 | 9 | 770 | 4.44 | 39,973.31 |
| tristar_centennial | 4,778,005 | 1,132 | 10 | 1,112 | 4.75 | 66,535.48 |

## VUMC physician fees

The $0.01 rate is one row: 74177, Cigna OAP All Commercial Plans, fee schedule 45, location `VWCH IMAGING READS AT VUH`, provider type Physician. It is a radiologist fee row, not a hospital price. Why this one row is a cent is still unknown, so treat it as a likely placeholder.

The bigger finding: `vumc_main` publishes physician and anesthesia fees in the same file as facility rates. `additional_generic_notes` carries `Provider Type:` on 3,832 of its 4,195 10-code rows (91%): Physician 1,962, Anesthesiologist 1,556, Nurse Anesthetist 314. A keyword search of the notes found no such rows in `ascension_west`, `ascension_midtown`, `vumc_clarksville`, or `tristar_centennial`. `vumc_wilson` is not downloaded yet and may share the pattern.

From `scratch/m2_penny.py`, median negotiated dollars at VUMC:

| code | with provider type | no provider type in the notes |
| --- | --- | --- |
| 66984 cataract | 158.76 | 2,514.63 |
| 29881 knee scope | 754.53 | 3,565.21 |
| 74177 CT | 115.73 | 380.14 |

The second column holds only rows where the note exists without a provider type. Rows with an empty note have higher medians still (for 66984, 6,996.00).

Without a fix, VUMC looks far cheaper than TriStar and Ascension for reasons that have nothing to do with price. M3 must flag these rows from the note and keep them out of hospital-to-hospital comparisons. Silver already keeps the note, so nothing needs reloading. Physician fees can still appear separately, labeled as such.
