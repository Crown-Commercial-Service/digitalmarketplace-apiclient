from enum import Enum, unique


@unique
class AuditTypes(Enum):

    # User account events
    create_user = "create_user"
    update_user = "update_user"
    invite_user = "invite_user"
    user_auth_failed = "user_auth_failed"
    contact_update = "contact_update"
    create_supplier = "create_supplier"
    supplier_update = "supplier_update"

    # Draft service lifecycle event
    create_draft_service = "create_draft_service"
    update_draft_service = "update_draft_service"
    update_draft_service_status = "update_draft_service_status"
    complete_draft_service = "complete_draft_service"
    publish_draft_service = "publish_draft_service"
    delete_draft_service = "delete_draft_service"

    # Live service lifecycle events
    import_service = "import_service"
    update_service = "update_service"
    update_service_admin = "update_service_admin"
    update_service_status = "update_service_status"
    update_service_supplier = "update_service_supplier"

    # Brief lifecycle events
    create_brief = "create_brief"
    update_brief = "update_brief"
    update_brief_status = "update_brief_status"
    create_brief_response = "create_brief_response"
    update_brief_response = "update_brief_response"
    submit_brief_response = "submit_brief_response"
    add_brief_clarification_question = "add_brief_clarification_question"
    delete_brief = "delete_brief"
    update_brief_framework_id = "update_brief_framework_id"

    # Supplier actions
    register_framework_interest = "register_framework_interest"
    view_clarification_questions = "view_clarification_questions"
    send_clarification_question = "send_clarification_question"
    send_application_question = "send_application_question"
    answer_selection_questions = "answer_selection_questions"
    update_declaration_answers = "update_declaration_answers"
    agree_framework_variation = "agree_framework_variation"
    update_supplier_framework = "update_supplier_framework"

    # Framework agreements
    create_agreement = "create_agreement"
    update_agreement = "update_agreement"
    upload_signed_agreement = "upload_signed_agreement"
    sign_agreement = "sign_agreement"
    upload_countersigned_agreement = "upload_countersigned_agreement"
    countersign_agreement = "countersign_agreement"
    delete_countersigned_agreement = "delete_countersigned_agreement"
    delete_supplier_framework_declaration = "delete_supplier_framework_declaration"

    # Framework lifecycle
    create_framework = "create_framework"
    framework_update = "framework_update"

    # Admin actions
    snapshot_framework_stats = "snapshot_framework_stats"
    create_buyer_email_domain = "create_buyer_email_domain"

    # Projects
    create_project = "create_project"
    create_project_search = "create_project_search"
    lock_project = "lock_project"
    downloaded_project = "downloaded_project"
    update_project = "update_project"

    # Outcomes
    create_outcome = "create_outcome"
    complete_outcome = "complete_outcome"
    update_outcome = "update_outcome"

    # Mailing list actions
    mailing_list_subscription = "mailing_list_subscription"

    @staticmethod
    def is_valid_audit_type(test_audit_type):

        for name, audit_type in AuditTypes.__members__.items():
            if audit_type.value == test_audit_type:
                return True
        return False
