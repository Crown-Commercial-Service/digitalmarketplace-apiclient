
def framework(status="open", slug="g-cloud-7", name=None, clarification_questions_open=True, lots=None):
    if slug == "g-cloud-7":
        name = "G-Cloud 7"
    elif slug == "digital-outcomes-and-specialists":
        name = "Digital Outcomes and Specialists"
    elif slug == "digital-outcomes-and-specialists-2":
        name = "Digital Outcomes and Specialists 2"
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
          user_id=123,
          framework_name="Digital Outcomes and Specialists",
          framework_framework="digital-outcomes-and-specialists",
          clarification_questions=None,
          clarification_questions_closed=False):
    brief = {
        "briefs": {
            "id": 1234,
            "title": "I need a thing to do a thing",
            "frameworkSlug": framework_slug,
            "frameworkName": framework_name,
            "frameworkFramework": framework_framework,
            "lotSlug": lot_slug,
            "status": status,
            "users": [{"active": True,
                       "role": "buyer",
                       "emailAddress": "buyer@email.com",
                       "id": user_id,
                       "name": "Buyer User"}],
            "createdAt": "2016-03-29T10:11:12.000000Z",
            "updatedAt": "2016-03-29T10:11:13.000000Z",
            "clarificationQuestions": clarification_questions or [],
        }
    }
    if status in ("live", "closed"):
        brief['briefs']['publishedAt'] = "2016-03-29T10:11:14.000000Z"
        brief['briefs']['applicationsClosedAt'] = "2016-04-07T00:00:00.000000Z"
        brief['briefs']['clarificationQuestionsClosedAt'] = "2016-04-02T00:00:00.000000Z"
        brief['briefs']['clarificationQuestionsAreClosed'] = clarification_questions_closed

    return brief
