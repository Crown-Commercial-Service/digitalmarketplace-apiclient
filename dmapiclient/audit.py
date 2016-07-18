from enum import Enum, unique


@unique
class AuditTypes(Enum):

    # User account events
    create_user = "create_user"
    update_user = "update_user"
    invite_user = "invite_user"
    user_auth_failed = "user_auth_failed"
    contact_update = "contact_update"
    supplier_update = "supplier_update"

    # Draft service lifecycle event
    create_draft_service = "create_draft_service"
    update_draft_service = "update_draft_service"
    update_draft_service_status = "update_draft_service_status"
    complete_draft_service = "complete_draft_service"
    publish_draft_service = "publish_draft_service"
    delete_draft_service = "delete_draft_service"

    # Live service lifecycle events
    update_service = "update_service"
    import_service = "import_service"
    update_service_status = "update_service_status"

    # Brief lifecycle events
    create_brief = "create_brief"
    update_brief = "update_brief"
    update_brief_status = "update_brief_status"
    create_brief_response = "create_brief_response"
    add_brief_clarification_question = "add_brief_clarification_question"
    delete_brief = "delete_brief"

    # Supplier actions
    register_framework_interest = "register_framework_interest"
    view_clarification_questions = "view_clarification_questions"
    send_clarification_question = "send_clarification_question"
    send_application_question = "send_application_question"
    answer_selection_questions = "answer_selection_questions"

    # Framework agreements
    upload_signed_agreement = "upload_signed_agreement"

    # Framework lifecycle
    create_framework = "create_framework"
    framework_update = "framework_update"

    # Admin actions
    upload_countersigned_agreement = "upload_countersigned_agreement"
    delete_countersigned_agreement = "delete_countersigned_agreement"
    snapshot_framework_stats = "snapshot_framework_stats"

    @staticmethod
    def is_valid_audit_type(test_audit_type):

        for name, audit_type in AuditTypes.__members__.items():
            if audit_type.value == test_audit_type:
                return True
        return False
