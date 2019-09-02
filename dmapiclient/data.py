from __future__ import unicode_literals
from .audit import AuditTypes
from .base import BaseAPIClient, logger, make_iter_method
from .errors import HTTPError


class DataAPIClient(BaseAPIClient):
    def init_app(self, app):
        self._base_url = app.config['DM_DATA_API_URL']
        self._auth_token = app.config['DM_DATA_API_AUTH_TOKEN']

    # Audit Events

    def find_audit_events(
            self,
            audit_type=None,
            audit_date=None,
            page=None,
            per_page=None,
            acknowledged=None,
            object_type=None,
            object_id=None,
            latest_first=None,
            earliest_for_each_object=None,
            user=None,
            data_supplier_id=None,
    ):

        params = {
            "acknowledged": acknowledged,
            "audit-date": audit_date,
            "data-supplier-id": data_supplier_id,
            "earliest_for_each_object": earliest_for_each_object,
            "latest_first": latest_first,
            "object-id": object_id,
            "object-type": object_type,
            "page": page,
            "per_page": per_page,
            "user": user,
        }

        if audit_type:
            if not isinstance(audit_type, AuditTypes):
                raise TypeError("Must be an AuditTypes")
            params["audit-type"] = audit_type.value

        return self._get(
            "/audit-events",
            params=params
        )

    def get_audit_event(self, audit_event_id):
        return self._get(
            "/audit-events/{}".format(audit_event_id)
        )

    find_audit_events_iter = make_iter_method('find_audit_events', 'auditEvents')
    find_audit_events_iter.__name__ = str("find_audit_events_iter")

    def acknowledge_audit_event(self, audit_event_id, user):
        return self._post_with_updated_by(
            "/audit-events/{}/acknowledge".format(audit_event_id),
            data={},
            user=user,
        )

    def acknowledge_service_update_including_previous(self, service_id, audit_event_id, user):
        return self._post_with_updated_by(
            "/services/{}/updates/acknowledge".format(service_id),
            data={"latestAuditEventId": audit_event_id},
            user=user,
        )

    def create_audit_event(self, audit_type, user=None, data=None, object_type=None, object_id=None):
        if not isinstance(audit_type, AuditTypes):
            raise TypeError("Must be an AuditTypes")
        if data is None:
            data = {}
        payload = {
            "type": audit_type.value,
            "data": data,
        }
        if user is not None:
            payload['user'] = user
        if object_type is not None:
            payload['objectType'] = object_type
        if object_id is not None:
            payload['objectId'] = object_id

        return self._post(
            '/audit-events',
            data={'auditEvents': payload})

    # Suppliers

    def find_suppliers(
        self, prefix=None, page=None, framework=None, duns_number=None, company_registration_number=None, name=None
    ):
        params = {}
        if prefix:
            params["prefix"] = prefix
        if name:
            params["name"] = name
        if page is not None:
            params['page'] = page
        if framework is not None:
            params['framework'] = framework
        if duns_number is not None:
            params['duns_number'] = duns_number
        if company_registration_number is not None:
            params['company_registration_number'] = company_registration_number

        return self._get(
            "/suppliers",
            params=params
        )

    find_suppliers_iter = make_iter_method('find_suppliers', 'suppliers')
    find_suppliers_iter.__name__ = str("find_suppliers_iter")

    def get_supplier(self, supplier_id):
        return self._get(
            "/suppliers/{}".format(supplier_id)
        )

    def create_supplier(self, supplier):
        return self._post(
            "/suppliers",
            data={"suppliers": supplier},
        )

    def update_supplier(self, supplier_id, supplier, user):
        return self._post_with_updated_by(
            "/suppliers/{}".format(supplier_id),
            data={
                "suppliers": supplier,
            },
            user=user,
        )

    def update_contact_information(self, supplier_id, contact_id,
                                   contact, user):
        return self._post_with_updated_by(
            "/suppliers/{}/contact-information/{}".format(
                supplier_id, contact_id),
            data={
                "contactInformation": contact,
            },
            user=user,
        )

    def remove_contact_information_personal_data(self, supplier_id, contact_id, user):
        return self._post_with_updated_by(
            "/suppliers/{}/contact-information/{}/remove-personal-data".format(supplier_id, contact_id),
            data={},
            user=user,
        )

    def get_framework_interest(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks/interest".format(supplier_id)
        )

    def register_framework_interest(self, supplier_id, framework_slug, user):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={},
            user=user,
        )

    def find_supplier_declarations(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks".format(supplier_id)
        )

    def get_supplier_declaration(self, supplier_id, framework_slug):
        response = self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )
        return {'declaration': response['frameworkInterest']['declaration']}

    def set_supplier_declaration(self, supplier_id, framework_slug, declaration, user):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(supplier_id, framework_slug),
            data={
                "declaration": declaration
            },
            user=user
        )

    def update_supplier_declaration(self, supplier_id, framework_slug, declaration_update, user):
        return self._patch_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(supplier_id, framework_slug),
            data={
                "declaration": declaration_update,
            },
            user=user
        )

    def remove_supplier_declaration(self, supplier_id, framework_slug, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(
                supplier_id, framework_slug),
            data={},
            user=user
        )

    def get_supplier_frameworks(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks".format(supplier_id)
        )

    def get_supplier_framework_info(self, supplier_id, framework_slug):
        return self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )

    def set_framework_result(self, supplier_id, framework_slug, is_on_framework, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"onFramework": is_on_framework},
            },
            user=user,
        )

    def set_supplier_framework_allow_declaration_reuse(self, supplier_id, framework_slug, allow, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"allowDeclarationReuse": allow},
            },
            user=user,
        )

    def set_supplier_framework_prefill_declaration(
        self,
        supplier_id,
        framework_slug,
        prefill_declaration_from_framework_slug,
        user,
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"prefillDeclarationFromFrameworkSlug": prefill_declaration_from_framework_slug},
            },
            user=user,
        )

    def set_supplier_framework_application_company_details_confirmed(
        self,
        supplier_id,
        framework_slug,
        application_company_details_confirmed,
        user,
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"applicationCompanyDetailsConfirmed": application_company_details_confirmed},
            },
            user=user,
        )

    def register_framework_agreement_returned(self, supplier_id, framework_slug, user, uploader_user_id=None):
        framework_interest_dict = {
            "agreementReturned": True,
        }
        if uploader_user_id is not None:
            framework_interest_dict['agreementDetails'] = {'uploaderUserId': uploader_user_id}

        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={"frameworkInterest": framework_interest_dict},
            user=user,
        )

    def unset_framework_agreement_returned(self, supplier_id, framework_slug, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {
                    "agreementReturned": False,
                },
            },
            user=user,
        )

    def update_supplier_framework_agreement_details(self, supplier_id, framework_slug, agreement_details, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {
                    "agreementDetails": agreement_details
                },
            },
            user=user,
        )

    def register_framework_agreement_countersigned(self, supplier_id, framework_slug, user):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"countersigned": True},
            },
            user=user,
        )

    def agree_framework_variation(self, supplier_id, framework_slug, variation_slug, agreed_user_id, user):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}/variation/{}".format(
                supplier_id, framework_slug, variation_slug),
            data={
                "agreedVariations": {"agreedUserId": agreed_user_id},
            },
            user=user,
        )

    def find_framework_suppliers(self, framework_slug, agreement_returned=None, statuses=None, with_declarations=True):
        '''
        :param agreement_returned: A boolean value that allows filtering by suppliers who have or have not
                                   returned their framework agreement. If 'agreement_returned' is set then
                                   any value for 'statuses' will be ignored.
        :param statuses: A comma-separated list of the statuses of framework agreements that should be returned.
                         Valid statuses are: signed, on-hold, approved and countersigned.
        :param with_declarations: whether to include declaration data in returned supplierFrameworks
        '''
        params = {}
        if agreement_returned is not None:
            params['agreement_returned'] = bool(agreement_returned)
        if statuses is not None:
            params['status'] = statuses
        if with_declarations is not True:
            params['with_declarations'] = bool(with_declarations)
        return self._get(
            '/frameworks/{}/suppliers'.format(framework_slug),
            params=params
        )

    find_framework_suppliers_iter = make_iter_method('find_framework_suppliers', 'supplierFrameworks')
    find_framework_suppliers_iter.__name__ = str("find_framework_suppliers_iter")

    def export_suppliers(self, framework_slug):
        return self._get(
            "/suppliers/export/{}".format(framework_slug)
        )

    export_suppliers_iter = make_iter_method('export_suppliers', 'suppliers')
    export_suppliers_iter.__name__ = str("export_suppliers_iter")

    # Users

    def create_user(self, user):
        return self._post(
            "/users",
            data={
                "users": user,
            })

    def find_users(
        self,
        supplier_id=None,
        page=None,
        role=None,
        personal_data_removed=None,
        *,
        user_research_opted_in=None,
    ):
        params = {}
        if supplier_id is not None and role is not None:
            raise ValueError(
                "Cannot get users by both supplier_id and role")
        if supplier_id is not None:
            params['supplier_id'] = supplier_id
        if role is not None:
            params['role'] = role
        if page is not None:
            params['page'] = page
        if personal_data_removed is not None:
            params['personal_data_removed'] = personal_data_removed
        if user_research_opted_in is not None:
            params['user_research_opted_in'] = user_research_opted_in
        return self._get("/users", params=params)

    find_users_iter = make_iter_method('find_users', 'users')
    find_users_iter.__name__ = str("find_users_iter")

    def get_user(self, user_id=None, email_address=None):
        if user_id is not None and email_address is not None:
            raise ValueError(
                "Cannot get user by both user_id and email_address")
        elif user_id is not None:
            url = "/users/{}".format(user_id)
            params = {}
        elif email_address is not None:
            url = "/users"
            params = {"email_address": email_address}
        else:
            raise ValueError("Either user_id or email_address must be set")

        try:
            user = self._get(url, params=params)

            if isinstance(user['users'], list):
                user['users'] = user['users'][0]

            return user

        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def authenticate_user(self, email_address, password):
        try:
            response = self._post(
                '/users/auth',
                data={
                    "authUsers": {
                        "emailAddress": email_address,
                        "password": password,
                    }
                })
            return response if response else None
        except HTTPError as e:
            if e.status_code not in [400, 403, 404]:
                raise

    def update_user_password(self, user_id, new_password, updater="no logged-in user"):
        try:
            self._post_with_updated_by(
                '/users/{}'.format(user_id),
                data={
                    "users": {"password": new_password},
                },
                user=updater,
            )
            return True
        except HTTPError:
            return False

    def update_user(self,
                    user_id,
                    locked=None,
                    active=None,
                    role=None,
                    supplier_id=None,
                    name=None,
                    user_research_opted_in=None,
                    updater="no logged-in user"):
        fields = {}
        if locked is not None:
            fields.update({
                'locked': locked
            })

        if active is not None:
            fields.update({
                'active': active
            })

        if user_research_opted_in is not None:
            fields.update({
                'userResearchOptedIn': user_research_opted_in
            })

        if role is not None:
            fields.update({
                'role': role
            })

        if supplier_id is not None:
            fields.update({
                'supplierId': supplier_id
            })

        if name is not None:
            fields.update({
                'name': name
            })

        params = {
            "users": fields,
        }

        user = self._post_with_updated_by(
            '/users/{}'.format(user_id),
            data=params,
            user=updater,
        )

        logger.info("Updated user {user_id} fields {params}",
                    extra={"user_id": user_id, "params": params})
        return user

    def remove_user_personal_data(self, user_id, user):
        return self._post_with_updated_by("/users/{}/remove-personal-data".format(user_id), data={}, user=user)

    def export_users(self, framework_slug):
        return self._get(
            "/users/export/{}".format(framework_slug)
        )

    export_users_iter = make_iter_method('export_users', 'users')
    export_users_iter.__name__ = str("export_users_iter")

    def is_email_address_with_valid_buyer_domain(self, email_address):
        return self._get(
            "/users/check-buyer-email", params={'email_address': email_address}
        )['valid']

    def get_buyer_email_domains(self, page=None):
        params = {}
        if page is not None:
            params["page"] = page

        return self._get("/buyer-email-domains", params=params)

    get_buyer_email_domains_iter = make_iter_method("get_buyer_email_domains", "buyerEmailDomains")
    get_buyer_email_domains_iter.__name__ = str("get_buyer_email_domains_iter")

    def create_buyer_email_domain(self, buyer_email_domain, user):
        return self._post_with_updated_by(
            "/buyer-email-domains",
            data={
                "buyerEmailDomains": {"domainName": buyer_email_domain}
            },
            user=user,
        )

    def email_is_valid_for_admin_user(self, email_address):
        return self._get(
            "/users/valid-admin-email", params={'email_address': email_address}
        )['valid']

    # Services

    def find_draft_services(self, supplier_id, service_id=None, framework=None):

        params = {
            'supplier_id': supplier_id
        }
        if service_id is not None:
            params['service_id'] = service_id
        if framework is not None:
            params['framework'] = framework

        return self._get('/draft-services', params=params)

    find_draft_services_iter = make_iter_method('find_draft_services', 'services')
    find_draft_services_iter.__name__ = str("find_draft_services_iter")

    def get_draft_service(self, draft_id):
        return self._get(
            "/draft-services/{}".format(draft_id)
        )

    def delete_draft_service(self, draft_id, user):
        return self._delete_with_updated_by(
            "/draft-services/{}".format(draft_id),
            data={},
            user=user,
        )

    def copy_draft_service_from_existing_service(self, service_id, user, data={}):
        return self._put_with_updated_by(
            "/draft-services/copy-from/{}".format(service_id),
            data=data,
            user=user,
        )

    def copy_published_from_framework(self, framework_slug, lot_slug, user, data={}):
        return self._post_with_updated_by(
            "/draft-services/{}/{}/copy-published-from-framework".format(framework_slug, lot_slug),
            data=data,
            user=user,
        )

    def copy_draft_service(self, draft_id, user):
        return self._post_with_updated_by(
            "/draft-services/{}/copy".format(draft_id),
            data={},
            user=user,
        )

    def update_draft_service(self, draft_id, service, user, page_questions=None):
        data = {
            "services": service,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._post_with_updated_by("/draft-services/{}".format(draft_id), data=data, user=user)

    def complete_draft_service(self, draft_id, user):
        return self._post_with_updated_by(
            "/draft-services/{}/complete".format(draft_id),
            data={},
            user=user,
        )

    def update_draft_service_status(self, draft_id, status, user):
        data = {
            "services": {"status": status},
        }

        return self._post_with_updated_by(
            "/draft-services/{}/update-status".format(draft_id),
            data=data,
            user=user,
        )

    def publish_draft_service(self, draft_id, user):
        return self._post_with_updated_by(
            "/draft-services/{}/publish".format(draft_id),
            data={},
            user=user,
        )

    def create_new_draft_service(self, framework_slug, lot, supplier_id, data, user, page_questions=None):
        service_data = data.copy()
        service_data.update({
            "frameworkSlug": framework_slug,
            "lot": lot,
            "supplierId": supplier_id,
        })

        return self._post_with_updated_by(
            "/draft-services",
            data={
                "services": service_data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def get_archived_service(self, archived_service_id):
        return self._get("/archived-services/{}".format(archived_service_id))

    def get_service(self, service_id):
        try:
            return self._get(
                "/services/{}".format(service_id))
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def find_services(self, supplier_id=None, framework=None, status=None, page=None, lot=None):
        params = {
            'supplier_id': supplier_id,
            'framework': framework,
            'lot': lot,
            'status': status,
            'page': page,
        }

        return self._get("/services", params=params)

    find_services_iter = make_iter_method('find_services', 'services')
    find_services_iter.__name__ = str("find_services_iter")

    def update_service(self, service_id, service, user, user_role='', *, wait_for_index: bool = True):
        return self._post_with_updated_by(
            "/services/{}?{}{}".format(
                service_id,
                "&wait-for-index={}".format(str(wait_for_index).lower()),
                "&user-role={}".format(user_role) if user_role else "",
            ),
            data={
                "services": service,
            },
            user=user,
        )

    def update_service_status(self, service_id, status, user):
        return self._post_with_updated_by(
            "/services/{}/status/{}".format(service_id, status),
            data={},
            user=user,
        )

    def revert_service(self, service_id, archived_service_id, user):
        return self._post_with_updated_by(
            "/services/{}/revert".format(service_id),
            data={"archivedServiceId": int(archived_service_id)},
            user=user,
        )

    def find_frameworks(self):
        return self._get("/frameworks")

    def get_framework(self, slug):
        return self._get("/frameworks/{}".format(slug))

    def update_framework(self, framework_slug, data, user):
        return self._post_with_updated_by(
            "/frameworks/{}".format(framework_slug),
            data={"frameworks": data},
            user=user
        )

    def transition_dos_framework(self, framework_slug, expiring_framework_slug, user):
        return self._post_with_updated_by(
            "/frameworks/transition-dos/{}".format(framework_slug),
            data={"expiringFramework": expiring_framework_slug},
            user=user,
        )

    def get_interested_suppliers(self, framework_slug):
        return self._get(
            "/frameworks/{}/interest".format(framework_slug)
        )

    def get_framework_stats(self, framework_slug):
        return self._get(
            "/frameworks/{}/stats".format(framework_slug))

    # Buyer briefs

    def create_brief(self, framework_slug, lot_slug, user_id, data, updated_by, page_questions=None):
        brief_data = data.copy()
        brief_data.update({
            "frameworkSlug": framework_slug,
            "lot": lot_slug,
            "userId": user_id,
        })
        return self._post_with_updated_by(
            "/briefs",
            data={
                "briefs": brief_data,
                "page_questions": page_questions or [],
            },
            user=updated_by,
        )

    def copy_brief(self, brief_id, updated_by):
        return self._post_with_updated_by(
            "/briefs/{}/copy".format(brief_id),
            data={},
            user=updated_by,
        )

    def update_brief(self, brief_id, brief, updated_by, page_questions=None):
        return self._post_with_updated_by(
            "/briefs/{}".format(brief_id),
            data={
                "briefs": brief,
                "page_questions": page_questions or [],
            },
            user=updated_by,
        )

    def update_brief_award_brief_response(self, brief_id, brief_response_id, updated_by):
        return self._post_with_updated_by(
            "/briefs/{}/award".format(brief_id),
            data={"briefResponseId": brief_response_id},
            user=updated_by,
        )

    def update_brief_award_details(self, brief_id, brief_response_id, award_details, updated_by):
        return self._post_with_updated_by(
            "/briefs/{}/award/{}/contract-details".format(brief_id, brief_response_id),
            data={"awardDetails": award_details},
            user=updated_by,
        )

    def publish_brief(self, brief_id, user):
        return self._post_with_updated_by(
            "/briefs/{}/publish".format(brief_id),
            data={},
            user=user,
        )

    def cancel_brief(self, brief_id, user):
        return self._post_with_updated_by(
            "/briefs/{}/cancel".format(brief_id),
            data={},
            user=user,
        )

    def withdraw_brief(self, brief_id, user):
        return self._post_with_updated_by(
            "/briefs/{}/withdraw".format(brief_id),
            data={},
            user=user,
        )

    def update_brief_as_unsuccessful(self, brief_id, user):
        return self._post_with_updated_by(
            "/briefs/{}/unsuccessful".format(brief_id),
            data={},
            user=user,
        )

    def get_brief(self, brief_id):
        return self._get(
            "/briefs/{}".format(brief_id))

    def find_briefs(
        self, user_id=None, status=None, framework=None, lot=None, page=None, human=None, with_users=None,
        with_clarification_questions=None, closed_on=None, withdrawn_on=None, cancelled_on=None, unsuccessful_on=None
    ):
        return self._get(
            "/briefs",
            params={"user_id": user_id,
                    "framework": framework,
                    "lot": lot,
                    "status": status,
                    "page": page,
                    "human": human,
                    "with_users": with_users,
                    "with_clarification_questions": with_clarification_questions,
                    "closed_on": closed_on,
                    "withdrawn_on": withdrawn_on,
                    "cancelled_on": cancelled_on,
                    "unsuccessful_on": unsuccessful_on
                    }
        )

    find_briefs_iter = make_iter_method('find_briefs', 'briefs')
    find_briefs_iter.__name__ = str("find_briefs_iter")

    def delete_brief(self, brief_id, user):
        return self._delete_with_updated_by(
            "/briefs/{}".format(brief_id),
            data={},
            user=user,
        )

    def is_supplier_eligible_for_brief(self, supplier_id, brief_id):
        return len(self._get(
            "/briefs/{}/services".format(brief_id),
            params={"supplier_id": supplier_id}
        )['services']) > 0

    def create_brief_response(self, brief_id, supplier_id, data, user, page_questions=None):
        data = dict(data, briefId=brief_id, supplierId=supplier_id)
        return self._post_with_updated_by(
            "/brief-responses",
            data={
                "briefResponses": data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def update_brief_response(self, brief_response_id, data, user, page_questions=None):
        return self._post_with_updated_by(
            "/brief-responses/{}".format(brief_response_id),
            data={
                "briefResponses": data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def submit_brief_response(self, brief_response_id, user):
        return self._post_with_updated_by(
            "/brief-responses/{}/submit".format(brief_response_id),
            data={},
            user=user,
        )

    def get_brief_response(self, brief_response_id):
        return self._get(
            "/brief-responses/{}".format(brief_response_id))

    def find_brief_responses(self, brief_id=None, supplier_id=None, status=None, framework=None, awarded_at=None):
        return self._get(
            "/brief-responses",
            params={
                "brief_id": brief_id,
                "supplier_id": supplier_id,
                "status": status,
                "framework": framework,
                "awarded_at": awarded_at
            })

    find_brief_responses_iter = make_iter_method('find_brief_responses', 'briefResponses')
    find_brief_responses_iter.__name__ = str("find_brief_responses_iter")

    def add_brief_clarification_question(self, brief_id, question, answer, user):
        return self._post_with_updated_by(
            "/briefs/{}/clarification-questions".format(brief_id),
            data={
                "clarificationQuestion": {
                    "question": question,
                    "answer": answer,
                }
            },
            user=user)

    # Agreements

    def get_framework_agreement(self, framework_agreement_id):
        return self._get(
            "/agreements/{}".format(framework_agreement_id))

    def create_framework_agreement(self, supplier_id, framework_slug, user):
        return self._post_with_updated_by(
            "/agreements",
            data={
                "agreement": {"supplierId": supplier_id, "frameworkSlug": framework_slug},
            },
            user=user
        )

    def update_framework_agreement(self, framework_agreement_id, framework_agreement, user):
        return self._post_with_updated_by(
            "/agreements/{}".format(framework_agreement_id),
            data={
                "agreement": framework_agreement,
            },
            user=user,
        )

    def sign_framework_agreement(self, framework_agreement_id, user, signed_agreement_details=None):
        data = {"agreement": {"signedAgreementDetails": signed_agreement_details}} if signed_agreement_details else {}
        return self._post_with_updated_by(
            "/agreements/{}/sign".format(framework_agreement_id),
            data=data,
            user=user,
        )

    def put_signed_agreement_on_hold(self, framework_agreement_id, user):
        return self._post_with_updated_by(
            "/agreements/{}/on-hold".format(framework_agreement_id),
            data={},
            user=user
        )

    def approve_agreement_for_countersignature(self, framework_agreement_id, user, user_id):
        return self._post_with_updated_by(
            "/agreements/{}/approve".format(framework_agreement_id),
            data={
                "agreement": {"userId": user_id}
            },
            user=user
        )

    def unapprove_agreement_for_countersignature(self, framework_agreement_id, user, user_id):
        return self._post_with_updated_by(
            "/agreements/{}/approve".format(framework_agreement_id),
            data={
                "agreement": {
                    "userId": user_id,
                    "unapprove": True,
                },
            },
            user=user
        )

    # Direct Award Projects

    def find_direct_award_projects(
        self,
        user_id=None,
        having_outcome=None,
        locked=None,
        page=None,
        latest_first=None,
        with_users=False,
    ):
        params = {
            "user-id": user_id,
            "page": page,
        }

        if latest_first is not None:
            params['latest-first'] = latest_first
        if having_outcome is not None:
            params['having-outcome'] = having_outcome
        if locked is not None:
            params['locked'] = locked
        if with_users:
            params['include'] = "users"

        return self._get(
            "/direct-award/projects",
            params=params,
        )

    find_direct_award_projects_iter = make_iter_method('find_direct_award_projects', 'projects')
    find_direct_award_projects_iter.__name__ = str("find_direct_award_projects_iter")

    def get_direct_award_project(self, project_id):
        return self._get("/direct-award/projects/{}".format(project_id))

    def create_direct_award_project(self, user_id, user_email, project_name):
        return self._post_with_updated_by(
            "/direct-award/projects",
            data={
                "project": {
                    "name": project_name,
                    "userId": user_id
                }
            },
            user=user_email
        )

    def find_direct_award_project_searches(self, project_id, user_id=None, page=None, only_active=None):
        params = {
            "user-id": user_id,
            "page": page,
        }

        if only_active is not None:
            params.update({'only-active': only_active})

        return self._get(
            "/direct-award/projects/{}/searches".format(project_id),
            params=params
        )

    find_direct_award_project_searches_iter = make_iter_method('find_direct_award_project_searches', 'searches')
    find_direct_award_project_searches_iter.__name__ = str("find_direct_award_project_searches_iter")

    def create_direct_award_project_search(self, user_id, user_email, project_id, search_url):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/searches".format(project_id),
            data={
                "search": {
                    "searchUrl": search_url,
                    "userId": user_id
                }
            },
            user=user_email
        )

    def get_direct_award_project_search(self, user_id, project_id, search_id):
        return self._get(
            "/direct-award/projects/{}/searches/{}".format(project_id, search_id),
            params={
                "user-id": user_id
            }
        )

    def find_direct_award_project_services(self, project_id, user_id=None, fields=[]):
        params = {"user-id": user_id}
        if fields:
            params.update({"fields": ','.join(fields)})

        return self._get(
            "/direct-award/projects/{}/services".format(project_id),
            params=params
        )

    find_direct_award_project_services_iter = make_iter_method('find_direct_award_project_services', 'services')
    find_direct_award_project_services_iter.__name__ = str("find_direct_award_project_services_iter")

    def lock_direct_award_project(self, user_email, project_id):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/lock".format(project_id),
            data={},
            user=user_email,
        )

    def record_direct_award_project_download(self, user_email, project_id):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/record-download".format(project_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_award(self, project_id, awarded_service_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/services/{}/award".format(project_id, awarded_service_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_cancelled(self, project_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/cancel".format(project_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_none_suitable(self, project_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/none-suitable".format(project_id),
            data={},
            user=user_email,
        )

    def mark_direct_award_project_as_still_assessing(self, project_id, user_email):
        return self._patch_with_updated_by(
            f"/direct-award/projects/{project_id}",
            data={"project": {"stillAssessing": True}},
            user=user_email,
        )

    def update_direct_award_project(self, project_id, project_data, user_email):
        return self._patch_with_updated_by(
            f"/direct-award/projects/{project_id}",
            data={"project": project_data},
            user=user_email,
        )

    # Outcomes

    def update_outcome(self, outcome_id, outcome_data, user_email):
        return self._put_with_updated_by(
            "/outcomes/{}".format(outcome_id),
            data={
                "outcome": outcome_data,
            },
            user=user_email,
        )

    def get_outcome(self, outcome_id):
        return self._get("/outcomes/{}".format(outcome_id))

    def find_outcomes(self, completed=None, page=None):
        # we call this "find outcomes" for consistency with other methods, but it's not particularly useful for finding
        # specific outcomes yet due to the lack of filtering options
        return self._get(
            "/outcomes",
            params={
                "page": page,
                "completed": completed,
            },
        )

    find_outcomes_iter = make_iter_method("find_outcomes", "outcomes")
    find_outcomes_iter.__name__ = str("find_outcomes_iter")
