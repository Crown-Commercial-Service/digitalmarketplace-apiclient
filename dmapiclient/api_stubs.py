
def framework(status="open", slug="g-cloud-7", name=None, clarification_questions_open=True, lots=None):
    if slug == "g-cloud-7":
        name = "G-Cloud 7"
    elif slug == "digital-outcomes-and-specialists":
        name = "Digital Outcomes and Specialists"
    else:
        name = slug.replace("-", " ").title()

    lots = lots or []

    return {
        "frameworks": {
            "status": status,
            "clarificationQuestionsOpen": clarification_questions_open,
            "name": name,
            "slug": slug,
            "lots": lots,
        }
    }


def lot(slug="some-lot", allows_brief=False, one_service_limit=False):
    return {
        "id": 1,
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "allowsBrief": allows_brief,
        "oneServiceLimit": one_service_limit,
    }


def brief(status="draft",
          framework_slug="digital-outcomes-and-specialists",
          lot_slug="digital-specialists",
          user_id=123):
    return {
        "briefs": {
            "id": 1234,
            "frameworkSlug": framework_slug,
            "lotSlug": lot_slug,
            "status": status,
            'users': [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": user_id,
                       "name": "Buyer User"}],
        }
    }
