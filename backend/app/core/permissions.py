PERMISSION_CATALOG = (
    ("dashboard.view", "View dashboard", "View dashboard summaries and performance", "Core"),
    ("cases.view", "View cases", "View cases within the user's data scope", "Core"),
    ("cases.view_all", "View all cases", "Bypass assigned-only case scope", "Core"),
    ("cases.create", "Create cases", "Create cases and initial visits", "Core"),
    ("cases.edit", "Edit cases", "Edit any visible case", "Core"),
    ("cases.edit_assigned", "Edit assigned cases", "Edit permitted fields on assigned work", "Core"),
    ("cases.delete", "Delete cases", "Permanently delete cases", "Core"),
    ("search.view", "Use search", "Access global case search", "Core"),
    ("reports.view", "View reports", "View reports within normal scope", "Core"),
    ("reports.view_own", "View own reports", "View assigned-only reports", "Core"),
    ("reports.view_all", "View all reports", "Bypass assigned-only report scope", "Core"),
    ("settings.view", "View settings", "View and update own profile settings", "Core"),
    ("users.view", "View users", "List and view user accounts", "Users"),
    ("users.create", "Create users", "Create user accounts", "Users"),
    ("users.edit", "Edit users", "Edit identity, role, and Executive links", "Users"),
    ("users.deactivate", "Activate/deactivate users", "Change account active status", "Users"),
    ("users.reset_password", "Reset passwords", "Reset another user's password", "Users"),
    ("users.manage_permissions", "Manage permissions", "Grant and remove user permissions", "Users"),
    ("masters.view", "View masters", "View master data", "Masters"),
    ("companies.manage", "Manage companies", "Create and edit companies", "Masters"),
    ("banks.manage", "Manage banks", "Create, edit, and delete banks and branches", "Masters"),
    ("districts.manage", "Manage districts", "Create and edit districts", "Masters"),
    ("executives.manage", "Manage executives", "Create, edit, and delete executives", "Masters"),
    ("loan_types.manage", "Manage loan types", "Create, edit, and delete loan types", "Masters"),
    ("product_types.manage", "Manage product types", "Create, edit, and delete product types", "Masters"),
    ("billing.view", "View billing", "View billing records and monthly billing", "Billing"),
    ("billing.rate_master", "Manage rate masters", "View and manage payout rate masters", "Billing"),
    ("billing.payment_register", "Manage payment register", "Update Executive and bank payments", "Billing"),
    ("billing.dashboard", "View billing dashboard", "View billing dashboard", "Billing"),
    ("billing.finalize", "Finalize billing", "Finalize billing months", "Billing"),
    ("billing.reopen", "Reopen billing", "Reopen finalized billing months", "Billing"),
    ("billing.regenerate", "Regenerate billing", "Regenerate reopened billing snapshots", "Billing"),
    ("billing.delete", "Delete billing", "Delete billing records", "Billing"),
    ("notifications.view", "View notifications", "View scoped notifications", "Operations"),
    ("followups.view", "View follow-ups", "View scoped follow-ups", "Operations"),
    ("visits.create", "Create visits", "Create case visits", "Operations"),
    ("visits.edit", "Edit visits", "Edit visits within data scope", "Operations"),
    ("visits.delete", "Delete visits", "Delete visits", "Operations"),
)

ALL_PERMISSION_CODES = frozenset(row[0] for row in PERMISSION_CATALOG)
DEFAULT_ROLE_PERMISSIONS = {
    "Manager": frozenset({"dashboard.view", "cases.view", "cases.create", "cases.edit", "search.view", "reports.view", "settings.view"}),
    "Executive": frozenset({"dashboard.view", "cases.view", "cases.edit_assigned", "search.view", "reports.view_own", "settings.view"}),
}


def default_permissions(role: str) -> set[str]:
    return set(ALL_PERMISSION_CODES if role == "Admin" else DEFAULT_ROLE_PERMISSIONS.get(role, ()))
