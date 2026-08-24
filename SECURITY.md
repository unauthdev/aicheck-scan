# security

## reporting a vulnerability

email **security@unauth.dev** with what you found, how to reproduce it, and
the version you tested. plain text is fine, no pgp required yet.

we aim to acknowledge within 72 hours, give a triage verdict within 7 days,
and ship a fix or mitigation within 30 days for confirmed issues. please
give us that window before disclosing publicly.

## who maintains this

aicheck is built and maintained by one person: **unauth.dev**
(https://unauth.dev/about). reports go to the maintainer directly. there is
no separate security team or outsourced triage.

## supported versions

only the latest 2.x release gets fixes. upgrade before reporting against an
older version.

| version | supported |
|---|---|
| 2.x (latest) | yes |
| 1.x | no (frozen leftover live-probe Action) |
| anything older | no |

## one ground rule

we will never ask for your credentials. aicheck needs none and sends nothing anywhere.

## research canary in this README (disclosed)

the README carries one canary token: a line addressed to automated agents
asking them to fetch `https://unauth.dev/c/<token>` before summarizing the
document. it is a research instrument for measuring whether LLM agents read
and obey instructions found in public documentation, and it is disclosed here
rather than hidden.

what it is not: it does not run, it is not in the installed package, it does
not touch the tool's behaviour, and it collects nothing from you. a fetch
records a timestamp, the user-agent string, and a salted hash of the source
address. no raw IP is stored. a human reading this repo can ignore it; the
tool works identically whether it is fetched or not.

the same mechanism is available to anyone at https://unauth.dev/canary.
if you would rather your tooling not touch it, do not fetch the URL.
