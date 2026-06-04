# Banking Onboarding Use Cases

## Consumer Deposit Onboarding

Starter template: `template_consumer_checking_onboarding`.

Steps:

- Eligibility.
- Personal information.
- Contact information.
- Address.
- Identity.
- Employment and income.
- Funding source.
- Disclosures and consent.
- Document upload.
- Review and submit.
- Decision/result.

Built-in draft logic:

- Additional residency questions when citizenship status is not `US Citizen`.
- Manual review routing when applicant age is under 18.
- Placeholder KYC and document verification actions before final submission.

## Small Business Deposit Onboarding

Starter template: `template_small_business_deposit_onboarding`.

Steps:

- Business information.
- Entity details.
- Tax information.
- Business address.
- Authorized signer.
- Beneficial ownership.
- Expected activity.
- Documents.
- Disclosures and consent.
- Review and submit.
- Manual review/result.

Built-in draft logic:

- Beneficial owner collection for LLCs, corporations, and partnerships.
- Placeholder KYB and OFAC/sanctions actions.
- Human review required before final result.

## Loan Prequalification

Starter template: `template_loan_prequalification`.

Steps:

- Product selection.
- Applicant information.
- Income.
- Housing.
- Credit consent.
- Requested amount.
- Soft-pull placeholder.
- Decision/result.

Built-in draft logic:

- Credit consent before soft-pull placeholder.
- Credit bureau placeholder connector.
- FCRA, ECOA, UDAAP, and adverse action review flags.

