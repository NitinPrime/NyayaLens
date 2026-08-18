# Privacy

NyayaLens may receive sensitive descriptions of real-world disputes.

## What we ask

Avoid submitting unnecessary personally identifiable information (full names, Aadhaar numbers, bank account numbers, precise home addresses) unless you are running a private local instance and accept the risk.

## Local development

In the default local configuration, case text is stored in a SQLite file on your machine (`data/nyayalens.db`). Do not commit that file.

## Logging

The API is configured not to log full case descriptions or uploaded document contents by default. Analysis-run logs record stage, latency, retrieval count, and model name.

## Authentication

Optional JWT authentication can bind cases to a user. Demo cases remain inspectable for product evaluation. Server-side checks prevent access to another user's non-demo case when a `user_id` is set.

## Claims we do not make

This project does not claim DPDP or GDPR compliance unless those controls are implemented and independently assessed for a specific deployment.
