
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


def supplier(id=1234, contact_id=4321, other_company_registration_number=0, company_details_confirmed=True):
    data = {
        "suppliers": {
            "companiesHouseNumber": "12345678",
            "companyDetailsConfirmed": company_details_confirmed,
            "contactInformation": [
                {
                    "address1": "123 Fake Road",
                    "city": "Madeupolis",
                    "contactName": "Mr E Man",
                    "email": "mre@company.com",
                    "id": contact_id,
                    "links": {
                        "self": "http://localhost:5000/suppliers/{id}/contact-information/{contact_id}".format(
                            id=id, contact_id=contact_id
                        )
                    },
                    "phoneNumber": "01234123123",
                    "postcode": "A11 1AA",
                    "website": "https://www.mre.company"
                }
            ],
            "description": "I'm a supplier.",
            "dunsNumber": "123456789",
            "id": id,
            "links": {
                "self": "http://localhost:5000/suppliers/{id}".format(id=id)
            },
            "name": "My Little Company",
            "organisationSize": "micro",
            "registeredName": "My Little Registered Company",
            "registrationCountry": "country:GB",
            "service_counts": {
                "G-Cloud 9": 109,
                "G-Cloud 8": 108,
                "G-Cloud 7": 107,
                "G-Cloud 6": 106,
                "G-Cloud 5": 105,
            },
            "tradingStatus": "limited company",
            "vatNumber": "111222333"
        }
    }

    if other_company_registration_number:
        data['suppliers']['otherCompanyRegistrationNumber'] = other_company_registration_number
        # We allow one or other of these registration numbers, but not both
        del data['suppliers']['companiesHouseNumber']
        # Companies without a Companies House number aren't necessarily overseas, but they might well be
        data['suppliers']['registrationCountry'] = 'country:NZ'

    return data
