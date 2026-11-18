"""Curated proposed mappings, not a Security-team approval or measured evidence."""

ATLAS_REVISION = "f56c1468731d6428e5bf875263b4643b46d67437"
OWASP_REVISION = "eb418d2b5c202d74b58e41f3195f9aaaa93e0563"
ATLAS_URL = f"https://github.com/mitre-atlas/atlas-data/blob/{ATLAS_REVISION}/dist/ATLAS.yaml"
OWASP_URL = (
    "https://github.com/OWASP/www-project-machine-learning-security-top-10/blob/"
    f"{OWASP_REVISION}/docs/ML01_2023-Input_Manipulation_Attack.md"
)


def threat_context():
    return {
        "schema_version": 1,
        "id": "sprint6-proposed-v1",
        "review_status": "proposed_security_review_pending",
        "references": [
            {
                "name": "MITRE ATLAS",
                "version": "5.6.0",
                "revision": ATLAS_REVISION,
                "url": ATLAS_URL,
            },
            {
                "name": "OWASP ML Security Top Ten",
                "version": "2023 draft",
                "revision": OWASP_REVISION,
                "url": OWASP_URL,
            },
        ],
        "mappings": [
            {
                "attacks": ["FGSM", "PGD", "CW-L2"],
                "mode": "white_box",
                "atlas": ["AML.T0043.000"],
                "owasp": ["ML01:2023"],
                "rationale_en": "Each optimizer uses the attacked model's gradients to manipulate inference inputs.",
                "rationale_ar": "كل خوارزمية بتستخدم تدرّجات الموديل المستهدف علشان تعدّل مدخلات التصنيف.",
            },
            {
                "attacks": ["FGSM", "PGD", "CW-L2"],
                "mode": "transfer",
                "atlas": ["AML.T0043.002"],
                "owasp": ["ML01:2023"],
                "rationale_en": "Craft on a distinct surrogate, then replay the same inputs on a target with no target feedback during crafting.",
                "rationale_ar": "بنولّد التعديل على موديل بديل مختلف، وبنختبر نفس المدخلات على الهدف من غير أي رد منه أثناء التوليد.",
            },
        ],
        "realism": {
            "scalar_feasibility": "policy_projected_feature_space_only",
            "coupled_structural_consistency": "not_established",
            "executable_realizability": "not_established",
            "preserved_behavior": "not_established",
            "security_review": "pending",
        },
        "optional_attacks": {
            "HopSkipJump": "not_implemented_not_run",
            "ZOO": "not_implemented_not_run",
        },
        "secondary_domain": "inactive_no_trained_ids_evidence",
        "lab": "not_authorized_not_run",
    }
