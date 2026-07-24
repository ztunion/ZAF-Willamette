# **A Zero Trust Framework for Last-Mile Access Authorization**

### *Root-Cause Analysis and Runtime Security Architecture for Workloads and AI Agents*

`1.0.2026.07.22`  
`michael@ztunion.com`

---

# **Executive Summary**

Every zero trust architecture eventually runs into the same problem: something, somewhere, has to hold a real credential. Service meshes authenticate workloads. API gateways enforce policy at the edge. Identity providers issue tokens. But when a client (a service, script, or AI agent) actually calls a downstream system, it typically holds a complete, reusable access credential: an API key, OAuth token, SSH private key, database password, or service-account secret. These credentials don't all work the same way, but if one is stolen, the attacker may be able to exercise the authority it represents.

This is the **Secret Zero** problem: a complete, reusable credential held by a workload, integration, script, or agent at the end of an otherwise carefully architected trust chain. If that component is compromised, the credential may be copied and exercised independently of the original workload. This pattern has contributed to major breaches involving cloud workloads, embedded administrative secrets, third-party integrations, and machine identities. The risk is increasing as organizations connect more service accounts, microservices, and autonomous AI agents to sensitive systems.

The Zero Trust Access Fabric (ZAF) is a runtime authorization architecture designed to eliminate this problem at the root, instead of managing around it. The question isn't how to better protect the secret the client holds. It's why the client needs to hold the secret at all. ZAF's answer, embodied in a patented system, is to separate proof of entitlement from possession of the credential itself. Most organizations can adopt ZAF without refactoring existing clients or servers. This paper covers the architecture, the problem it solves, and why that separation matters for anyone securing machine-to-machine access at scale.

# **The Problem: Secret Zero and the Limits of Current Approaches**

## **A sixty-year-old problem**

The tension between shared access and individual accountability isn't new. MIT's Compatible Time-Sharing System (CTSS), built under Fernando Corbató and first demonstrated in 1961, is widely credited as the first computer system to use passwords, a way to let multiple people share one machine while keeping each person's files separate \[1\]. It worked well enough for its era, and it set a pattern that's still in place today: a secret string, presented once, treated afterward as proof of identity. Six decades later, machine-to-machine access at internet scale still runs on a version of the same idea, and the underlying assumption, that whoever holds the credential is who they say they are, has never really been fixed, just patched around.

## **Why reusable credentials keep failing**

A bearer token can be used by whoever possesses and presents it. It doesn't require the holder to prove possession of separate cryptographic key material. API keys, passwords, and many OAuth access tokens work the same way in practice, even though they aren't all formally classified as bearer tokens. Other credentials, such as SSH private keys and proof-of-possession tokens, work differently, but they create a related custody risk: if an attacker obtains the means needed to use the credential, they may be able to exercise the authority assigned to the legitimate client.

Whether the credential is an API key stored in a configuration file, an SSH private key on a compromised host, a database password in an environment variable, or an OAuth token taken from a build pipeline, the central problem is the same: the client holds a complete, directly usable credential that can be copied or misused after compromise.

## **Why existing controls do not fully address the problem**

Organizations already use several effective controls to reduce credential and access risk: API gateways, outbound proxies and service-mesh egress gateways, dynamic-secret brokers, cloud IAM temporary credentials, attribute-based access control, certificate-bound and proof-of-possession tokens, and workload identity. Each addresses a different part of the problem: some strengthen identity, others shorten credential lifetime, restrict where a request can go, or keep a backend credential away from the original caller. These controls are valuable in their own right.

Their practical tradeoffs also differ. Depending on the control, adoption may require changes to the client, the destination, or both. Some approaches are difficult to use with older applications, third-party APIs, databases, or SaaS services. They may also introduce performance, availability, integration, licensing, or operational costs. Because those tradeoffs depend heavily on the product and deployment model, they aren't repeated for every control below.

ZAF is more focused than any of these controls: it asks whether the calling workload needs to possess a credential the downstream destination will accept directly. The table below summarizes what each control primarily protects, and what risk or privileged authority remains.

| Control | What it protects | What remains |
| ----- | ----- | ----- |
| API gateways | Authenticates and authorizes inbound requests, and may use a separate identity or credential to reach the backend | The gateway, or its managed identity, becomes a privileged point capable of invoking the backend |
| Outbound proxies / service-mesh egress | Routes, inspects, and applies policy to outbound traffic | If the proxy stores, obtains, or uses a downstream credential, it becomes a privileged credential-use point |
| Dynamic-secret brokers | Issues short-lived credentials and improves rotation, revocation, and auditing | In the common delivery model, the workload still receives a usable credential for the duration of its lease |
| Cloud IAM temporary credentials | Replaces long-lived access keys with credentials issued and refreshed automatically | A usable token is still available to the workload or its local platform, and the destination must trust the identity system |
| Attribute-based access control (ABAC) | Evaluates the caller, resource, requested action, environment, and other attributes before granting access | Doesn't by itself determine who holds the credential |
| Certificate-bound / proof-of-possession tokens | Prevents use of a stolen token without the associated private key | Compromised software inside the legitimate client may still invoke the key and token |
| Workload identity | Binds a short-lived identity to an authenticated workload or execution environment | Downstream systems that don't accept or federate with that identity may still require another credential |
| Credential exposure detection | Finds credentials that have already been exposed in code, pipelines, collaboration tools, and developer endpoints, and reconciles findings against vault coverage | The credential still has to be revoked or rotated, and the code and configuration that exposed it fixed, before the exposure actually closes |
| ZAF | Keeps the downstream credential out of the workload, and reauthorizes its use for each request | A malicious request may still be approved if it satisfies every required policy and authenticator check |

**API gateways** commonly authenticate an inbound caller and then use a separate identity or credential to reach the backend, whether through credential substitution, token exchange, credential injection, or a managed service identity. Some organizations also use gateways as managed facades for SaaS applications or other downstream services. A gateway doesn't necessarily store a static backend secret; it may obtain a short-lived token or use a managed identity instead. Either way, it becomes a privileged point in the request path, because it can make calls the backend will accept. That materially improves security by keeping a backend credential away from the original client, but it doesn't eliminate privileged authority. It moves that authority to the gateway and its supporting identity system.

Depending on implementation and solution, **outbound proxies and service-mesh egress gateways** can meaningfully reduce credential risk beyond the routing, inspection, and visibility they provide by default. Centralizing a credential in the proxy, rather than scattering it across application memory, is a real improvement. But if the proxy stores, obtains, or uses a downstream credential to do that, custody has simply moved to the proxy, not disappeared. And generic egress control by itself doesn't provide independent validation, multi-party approval, or per-request credential reconstruction; those capabilities aren't inherent to the proxy or service-mesh model.

**Dynamic-secret brokers** reduce the value of credential theft by issuing credentials with limited lifetimes, and they improve rotation, revocation, and auditing, often without requiring the destination to adopt a new authentication method. In the common model, the workload requests or receives a real credential and can use it until it expires or is revoked, so a compromised workload can use it during that window. Some deployments place an agent, proxy, or managed connector between the application and the destination so the application process never receives the credential directly; in that case, the intermediary becomes the privileged point that obtains and uses it instead.

**Cloud IAM temporary credentials** fix a lot of the risk you get from long-lived access keys, because the cloud platform issues, rotates, and refreshes them automatically — developers usually don't have to manage static secrets by hand. But “temporary” only means the credential expires eventually. Until it does, it's a complete, reusable credential, usable for every call the workload makes, whether the workload requested it directly or a platform component fetched it on the workload's behalf. If that workload gets compromised, an attacker can reuse the same token for every request until it expires. And if the attacker stays in, they can keep asking for new ones for as long as the identity system still thinks the workload is legitimate. This only works for destinations that trust the same identity system, though. Anything outside that — a third-party API, a SaaS tool, a database, an older system that only takes an API key or password — still needs its own separate credential.

**Attribute-based access control (ABAC)** determines whether a request should be allowed based on attributes of the caller, resource, requested action, environment, and other relevant conditions, and it can restrict access by workload identity, user, device posture, location, time, risk level, data classification, operation, or resource. That stops many insider or compromised-client actions that fall outside approved policy. But ABAC doesn't by itself determine who holds the credential used to carry out the request, and it can't always distinguish a malicious request from a legitimate one when both present the same policy-visible identity, action, and context. ZAF can use ABAC directly, evaluating the same kinds of attributes as part of its own per-request policy; ABAC is one of the authorization approaches ZAF applies, not a competing architecture.

**Certificate-bound and proof-of-possession tokens** stop an attacker who has stolen only the token from replaying it elsewhere, by requiring proof of the associated private key. But protecting that key is still the client's responsibility, and how well the scheme resists broader compromise depends entirely on how the key is generated, stored, and used. A hardware-backed or non-exportable key makes extraction much harder; if the key is exportable and both it and the token are stolen, the attacker can generally use them from infrastructure they control, unless additional restrictions apply. And even when the key can't be extracted, malicious software running inside the legitimate client can still invoke it and use the client's own token to issue unauthorized requests.

**Workload-identity systems** bind a short-lived identity to an authenticated workload or execution environment, reducing dependence on static secrets when the destination accepts that identity, federates with it, or can securely translate it into another accepted form. Not every hop needs to speak the same protocol; federation, token exchange, and trusted intermediaries can connect different identity systems. But a downstream service that only accepts an API key, password, database credential, or other legacy secret still reintroduces credential custody somewhere in the chain. A gateway or proxy can keep that credential away from the original workload, but the intermediary then becomes the privileged point authorized to use it. And a compromised workload can still exercise the authority assigned to its legitimate identity until policy, identity state, or another control restricts it.

**Credential exposure detection platforms** scan source code, CI/CD pipelines, collaboration tools, and developer endpoints for credentials that have already been exposed. Whether an exposure is actually remediated — the credential revoked or rotated, and the code and configuration that exposed it fixed — depends on separate incident-response practice. It is increasingly becoming a compliance expectation. But detection sits downstream of custody. Policy enforcement stays with the vault, PAM, and IGA systems it reports into — one vendor frames its own role as surfacing where reality diverges from that policy, not setting it \[17\]. The underlying credential still exists somewhere, complete and reusable, until someone remediates it. Before that happens, an exposed credential authenticates normally: the request passes verification, and audit logs record it as legitimate access \[17\].

This distinction runs through Zero Trust guidance more broadly: friction narrows a window, elimination closes it. Detection narrows the window by shortening dwell time on a credential that still exists. ZAF closes it outright — because the client never holds a complete credential, there's no exposure event left for a scanner to catch.

These controls, deployed correctly, meaningfully reduce risk. But none of them combines an opaque, workload-held reference; per-request authorization of both the caller and the action; quorum agreement from extensible, third-party-capable validators; brief, in-boundary credential reconstruction; a proxy designed to hold no standing credential; and independence from any single platform or third party. ZAF is built to provide exactly that combination, as the subsequent section explains.

# **The stakes are rising with agentic AI**

The problem is compounding as autonomous AI agents proliferate. Agents routinely need programmatic access to email, code repositories, financial systems, and internal tools, often stringing many of these calls together on their own, with no human reviewing each individual step before it happens. A single agent workflow might read an inbox, query a database based on what it finds there, and push a change to a deployment pipeline, all without a person in the loop between any of those steps. Each of those integration points is typically secured with a reusable credential, often an API key or OAuth token, and because it's rarely possible to predict in advance exactly which systems a given task will touch, the agent often holds standing access to all of them for as long as the broader task might require.

That standing access is what makes agent compromise different from a traditional compromised script. An attacker doesn't need to breach the agent's host or steal its credentials directly; they can instead manipulate the agent's own reasoning through prompt injection, hiding instructions inside a document, email, or web page the agent processes as part of its normal work. If that manipulation succeeds, the agent still has entirely legitimate credentials and legitimate authorization. It's simply been redirected to use them for something the original task never intended. An agent framework that's compromised, misconfigured, or manipulated this way can, in principle, exfiltrate or misuse every credential it has been handed.

One recent industry survey found that 69% of enterprises running AI agents share a single API key or credential across multiple agents rather than issuing each one its own scoped identity, meaning a single compromised agent can inherit the access of every other agent sharing that credential \[2\]. In multi-agent systems, where several agents coordinate on a task and call each other in addition to external services, a shared credential extends that exposure across the whole fleet, not just the one agent that gets compromised.

Non-human identities are now frequently the majority identity class in modern environments, and architecturally, they're the least equipped to resist credential theft. Human logins carry decades of accumulated defenses layered on top of the base credential: multi-factor authentication, behavioral anomaly detection, session timeouts tied to actual user activity, and the option to simply ask a person to re-verify when something looks off. Nearly all of those defenses assume a human is available to notice something is wrong and respond to a prompt, which an agent can't do. It will complete a challenge-response or re-authentication step exactly the way it completes any other instruction, with no way to tell whether the instruction itself should be trusted.

# **The Cost in Practice: Notable Credential-Related Incidents**

The Secret Zero problem is not theoretical. Major incidents have repeatedly shown what can happen when a workload, integration, script, or administrative component holds a complete credential that can be copied and reused independently. Other incidents involving stolen human or administrative credentials illustrate the broader related risk: once a system treats possession of a credential as sufficient authority, malicious use may be difficult to distinguish from legitimate access.

**Office of Personnel Management (2015).** Congressional testimony and reporting indicated that attackers used valid OPM credentials assigned to an employee of KeyPoint Government Solutions, a federal background-check contractor, to access OPM systems. The public record did not establish that KeyPoint itself caused the breach. The intrusion ultimately exposed background-investigation information for approximately 21.5 million people, including Social Security numbers and, for some individuals, fingerprint data. Because the credential was valid, the access looked legitimate to the system throughout. \[3\]

**Capital One (2019).** An attacker exploited a server-side request forgery (SSRF) vulnerability in a misconfigured web application firewall to query the AWS instance metadata service, retrieving temporary IAM credentials tied to an over-privileged role. Those credentials were then used to enumerate and download data from over 700 S3 buckets, exposing roughly 106 million records. The credentials themselves were legitimate and correctly issued. A central failure was that a compromised component could obtain and reuse them freely, with no additional proof of entitlement required. \[4\]

**Uber (2022).** Uber reported that an attacker likely obtained a contractor's corporate password after the contractor's personal device was infected with malware. Repeated multi-factor authentication prompts initially blocked access, but the contractor eventually approved one of them. According to contemporaneous security reporting, the attacker subsequently found a PowerShell script containing administrative credentials for Uber's privileged access management system, expanding the compromise across internal and cloud services. A reusable embedded credential converted limited initial access into broad administrative control. \[5\]

**Snowflake customer accounts (2024).** A financially motivated group used login credentials harvested years earlier by commodity infostealer malware from employee devices to log directly into roughly 165 customer accounts on the Snowflake cloud data platform. No vulnerability in Snowflake's own systems was involved. The affected accounts had never been required to use multi-factor authentication, so a bare username and password was sufficient for full account access. Victims included Ticketmaster/Live Nation (roughly 560 million customer records), AT\&T (call and text metadata for around 110 million customers), and Santander, among others. The credentials were years old and individually unremarkable. Nothing beyond the password stood between possessing them and using them. \[6\]

**Salesforce / Salesloft Drift (2025).** A Mandiant investigation commissioned by Salesloft found that an attacker accessed Salesloft's GitHub account, later reached Drift's AWS environment, and obtained OAuth tokens used by Drift customer integrations. The attacker then used the stolen tokens to access and exfiltrate data from customer Salesforce environments. Because the tokens represented an already-authorized integration, using them didn't require the attacker to obtain each customer's password or complete a new MFA challenge. \[7\]

**Fortinet FortiGate devices ("FortiBleed," 2026).** Fortinet reported a credential-harvesting campaign in which attackers reused credentials associated with earlier incidents and employed brute-force techniques against internet-accessible devices with weak password practices and no multi-factor authentication. Fortinet stated that the campaign did not involve a new Fortinet vulnerability. Once attackers had valid administrative or VPN credentials, they could authenticate to affected devices without exploiting any additional software flaw. \[8\]

**Klue (2026).** Klue reported that an attacker gained access through a compromised legacy credential associated with an integration service. The attacker used that access to obtain OAuth tokens connecting Klue to third-party platforms, including Salesforce, and subsequently accessed data in connected customer environments. The incident shows how a forgotten integration credential can provide an initial foothold and expose downstream authorization tokens long after the original integration was established. \[9\]

The incidents differ in both entry point and underlying control failure. Capital One, Uber, Salesloft Drift, and Klue most directly illustrate the credential-custody problem ZAF addresses: a compromised workload, script, or integration obtained a complete reusable credential that could be exercised without renewed authorization at the point of use. OPM, Snowflake, and Fortinet illustrate the broader danger of credential replay: once attackers obtained valid human, administrative, or VPN credentials, subsequent access was often accepted as legitimate.

Together, the incidents show a recurring security weakness: possession of a valid credential is frequently treated as sufficient authority, even when the surrounding context has changed. Verizon's 2025 Data Breach Investigations Report, covering more than 22,000 incidents and 12,000 confirmed breaches, found that credential abuse accounted for 22% of initial access, while stolen credentials were involved in 88% of breaches classified as Basic Web Application Attacks \[10\].

The trend shows no sign of slowing. Every fix that actually closes this gap trades convenience for infrastructure that has to be built and maintained, and under deadline pressure, most organizations ship the convenient version. Attacker-side economics have industrialized in the meantime. Infostealer malware and credential marketplaces make stolen credentials cheap and abundant, while forgotten legacy integrations, like the years-old credential behind the Klue breach above, sit unexamined until something breaks.

Non-human identities are multiplying far faster than the tooling meant to govern them, and each new identity typically brings its own credential, so the number of credentials in circulation is growing just as fast. One industry tracking effort found 28.65 million new hardcoded secrets exposed on public GitHub in 2025 alone, a 34% year-over-year jump, with AI-related credentials specifically the fastest-growing category at an 81% increase \[11\]. Shadow AI, meaning AI tools and agents adopted without security team visibility, adds a second, related pressure: IBM's 2025 Cost of a Data Breach Report found that 63% of the organizations studied lacked AI-governance policies to manage AI use or prevent the proliferation of shadow AI \[12\]. Neither has an established fix yet.

Agentic AI is repeating the same pattern, just faster than previous waves of technology did. Over sixty years, credentials have gotten shorter-lived, better-hashed, and more context-aware, but the industry still hasn't addressed the core question: whether the client needs to hold the credential at all. That's the assumption ZAF removes.

# **The ZAF Approach: Separating Custody from Usage**

## **The central idea**

ZAF's core move is to split the credential lifecycle into two roles that are almost always fused in conventional systems:

* **Custody:** actually possessing the plaintext, usable credential.

* **Usage:** presenting that credential to a downstream service to complete a request.

In a conventional deployment, the client does both. In ZAF, the client does neither. Instead:

The client holds only an opaque credential reference, a handle with no cryptographic value of its own. Stealing it gets an attacker nothing usable in isolation. Getting a client onto this model is typically a configuration change, not a code change. The real credential value the client used to store is simply replaced with this reference, and network steering (routing infrastructure most organizations already operate) directs the client's calls through the ZAF proxy without the client's code needing to know ZAF exists. In rare cases, such as a client with hardcoded network logic, or one that can't be pointed through a proxy at all, a small client-side change may still be needed. But this isn't the common case.

A Credential Management System (CMS), running inside a protected execution boundary, is the only component that reconstructs the real credential. It does so transiently: only after the client has established its entitlement and the specific request has been authorized, and only for immediate use by a proxy that completes the downstream call. The CMS and proxy operate within that boundary, where the plaintext credential stays protected in memory and is transmitted only to the intended downstream service over an authenticated, encrypted connection. The client never sees it, and it isn't retained after the request completes.

## **Distributed, quorum-based validation**

ZAF does not trust a single validator to make this decision. Access to a credential requires a quorum of independent authenticators, weighted by trust level, to agree that the requesting client is what it claims to be and that the requested action is authorized.

Authenticators can validate a client through:

* **Passive telemetry:** contextual signals such as network posture, behavioral history, or IP reputation, evaluated continuously.

* **Active challenge-response:** a cryptographic challenge answered using a hardware-anchored root of trust, such as a hardware security module or secure enclave. This is the same category of hardware used to protect a fingerprint or device-unlock key, applied here to proving a machine's identity.

Each authenticator independently validates the client and, if validation succeeds, securely releases its credential-reconstruction share to the CMS for the specific request. The CMS combines the shares only after all mandatory checks, trust-weight requirements, and the applicable quorum threshold have been satisfied. No individual authenticator possesses enough information to reconstruct the credential on its own. The CMS reconstructs the credential only inside its protected execution boundary and only for the authorized downstream request.

This model also supports customer-developed and third-party authenticators. An organization can register additional authenticators (a custom device-posture check, a behavioral model, a partner-supplied attestation service) and assign each an appropriate role and trust weight within the quorum.

# **How a Request Flows Through ZAF**

It's easiest to see the model concretely by walking through a single access request:

1. **The client makes its normal call.** A service, script, or AI agent calls the downstream system the way it always has. Network steering directs that call through the ZAF proxy.

2. **Proxy invokes the CMS.** The proxy forwards the request context to the CMS, which determines the current policy requirement: which authenticators must verify the client and confirm the action is authorized, and what quorum threshold applies given the request's risk attributes.

3. **Authenticators validate independently.** Each required authenticator performs its check, such as a hardware challenge-response, a telemetry assessment, or a behavioral comparison, without visibility into what the others are doing. It releases its credential-reconstruction share if validation succeeds.

4. **CMS assembles the credential, briefly.** Once enough credential-reconstruction shares are collected to meet the quorum, the CMS combines them inside its protected execution boundary, reconstructing the real credential for a single, transient use.

5. **Proxy completes the call.** The CMS hands the credential to the proxy, which uses it to complete the actual downstream request, in the exact format the destination already expects. The plaintext credential is never returned to the client and does not persist after use.

The result: at no point in this flow does the client hold anything an attacker could reuse.

This is a high-level view of the model. The specific authenticators, policy thresholds, and validation methods an organization configures can be adapted to different security targets and deployment contexts. One related capability is worth flagging as out of scope here: a more decentralized way of generating the underlying key shares, where no single party, not even the CMS, ever holds the complete picture, even briefly during setup. That's a stronger trust guarantee than the centralized approach described above, at the cost of meaningfully more implementation complexity, a tradeoff organizations can weigh based on their own risk tolerance.

# **Where ZAF Fits**

ZAF isn't a replacement for identity providers, service meshes, or API gateways. It's complementary to all of them, filling a gap they share. Identity providers establish who a caller is. Service meshes and gateways decide whether their traffic should be allowed. ZAF handles a narrower question underneath both: at the moment a credential is needed, who gets to hold it, and for how long?

Credential exposure detection platforms occupy an adjacent position alongside these, covering the code, ticket, chat, and developer-machine surface outside ZAF's scope. ZAF only protects credentials that have been registered with it. For credentials outside that boundary, it can be configured to either block them or allow pass-through while flagging the activity. The two aren't competing for the same layer.

This makes ZAF particularly relevant in four settings where the Secret Zero problem is most acute:

* Machine-to-machine and service-to-service access, where credentials are numerous, long-lived by default, and rarely rotated in practice.

* Reusable access credentials (API keys, OAuth tokens, SSH private keys, database passwords, service-account secrets), where compromise of the client may expose everything needed to exercise the credential's authority.

* Autonomous AI agents, where the number of integration points, and the difficulty of fully constraining agent behavior, make traditional bearer-credential distribution increasingly hard to sustain.

* Operational technology (OT) and legacy systems, where the runtime often can't support modern identity federation or run a local agent at all, but where network steering to a proxy typically doesn't require touching the device itself.

# **Alignment with NIST and NSA Guidance**

NIST and NSA guidance support principles underlying ZAF, although neither prescribes the ZAF architecture.

**NIST's Digital Identity Guidelines** require passwords to be protected against offline attack and collected over authenticated, encrypted channels. AAL2 requires two distinct authentication factors and a phishing-resistant option, while AAL3 requires phishing-resistant authentication using a hardware-protected, non-exportable key \[13\]. Although these requirements primarily address subscriber authentication, they reinforce a broader principle: authentication secrets should be strongly protected.

**NIST's Zero Trust Architecture** applies more directly to access decisions. It calls for least-privilege access, evaluated continually rather than granted once and trusted afterward, including reauthentication or reauthorization when needed \[14\]. A long-lived bearer credential, once issued, isn't reevaluated on that continual basis, which puts it at odds with Zero Trust principles, though NIST doesn't prescribe a specific mechanism or frequency for that reevaluation.

**NSA's Zero Trust Implementation Guidelines** similarly emphasize continuous verification and granular access control for users, devices, applications, workloads, and non-person entities, including PKI-based machine identity and ongoing verification of device trust \[15\]. ZAF's authenticator model addresses both: passive telemetry provides the continuous, ongoing verification NSA calls for, while the hardware-anchored challenge-response authenticator specifically satisfies the PKI-based machine identity requirement.

**NIST's key-management guidance** recommends limiting plaintext key exposure, restricting plaintext keys to protected containers, limiting key-management functions to authorized entities, and specifying split-knowledge procedures when divided custody is used \[16\].

NIST does not generally equate bearer access credentials with cryptographic keys, but both present a similar custody risk: unauthorized possession may enable the exercise of authority. ZAF brings that same key-management discipline to all downstream credentials.

Taken together, these publications provide a credible standards-based foundation for ZAF. The architecture applies established zero trust, machine-identity, and key-custody principles to downstream credential use: keeping reusable credentials out of workloads, mediating their use, and reauthorizing access at the point of request.

# **The ZAF Willamette Reference Implementation**

To ground the architecture in working code, ZTUnion has released ZAF Willamette, a reference implementation of the ZAF model, under the BSD 3-Clause Clear License at `github.com/ztunion/ZAF-Willamette`.

Willamette is explicitly scoped as an illustration of the ZAF model, not a canonical or production-complete implementation. It ships with a set of example authenticator signals (ASN, JA4 TLS fingerprint, IP CIDR range, country, and an allowed time window) chosen to demonstrate the pattern. Implementors can create and register their own authenticators using different signals entirely. These shipped signals are passive and contextual only. Willamette does not include the hardware-anchored active challenge-response path described earlier, under The ZAF Approach, and readers evaluating it as a benchmark of the full authorization model should account for that gap.

# **Why ZAF Is Significant, and Where It Leads**

ZAF targets the architectural root cause instead of adding another layer on top of it. Capital One, Uber, Salesloft Drift, and Klue all show what happens when a compromised workload, script, or integration holds a complete, reusable credential: it can be used again without any renewed proof that the original holder is still entitled to it. Existing mitigations reduce that risk by shortening credential lifetime, narrowing scope, or strengthening storage. ZAF takes the credential out of the workload entirely, mediates its use through a protected path, and reauthorizes each request before access completes. The proxy-based custody mechanism behind it has also been examined and found to be a novel, non-obvious invention, not just a pattern described in a white paper.

Timing matters too. Non-human identities, including service accounts, CI/CD pipelines, and AI agents, are multiplying faster than the controls meant to govern them, and each one introduces another credential that can be stolen or misused. This is especially acute in the operational technology and legacy systems described above, where compromised credentials can affect not only data, but also operations, availability, and public safety. A solution designed only for human logins is already behind where the risk now sits. ZAF treats machine and agent identities as the primary case from the start.

# **References**

\[1\] MIT News, "Professor Emeritus Fernando Corbató, MIT computing pioneer, dies at 93," 2019\. https://news.mit.edu/2019/mit-professor-emeritus-fernando-corby-corbato-computing-pioneer-dies-0715

\[2\] VentureBeat, "Shared API keys expose AI agents at 69% of enterprises, new VentureBeat research finds," Q2 2026 Agentic Security report, 2026\. https://venturebeat.com/security/shared-api-keys-expose-ai-agent-fleets-venturebeat-research

\[3\] U.S. House Committee on Oversight and Government Reform, *The OPM Data Breach: How the Government Jeopardized Our National Security for More than a Generation*, 2016; and U.S. Congress, *OPM Data Breach: Part II*, 2015\.

\[4\] U.S. Department of Justice, Western District of Washington, "United States v. Paige Thompson." https://www.justice.gov/usao-wdwa/united-states-v-paige-thompson

\[5\] Uber, "Security Update," September 2022; and BleepingComputer, "Uber Hacked, Internal Systems Breached and Vulnerability Reports Stolen," 2022\.

\[6\] Google Cloud Threat Intelligence, "UNC5537 Targets Snowflake Customer Instances for Data Theft and Extortion," 2024\. https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion

\[7\] Salesloft and Mandiant, "Update on Mandiant Drift and Salesloft Application Investigations," 2025; and Google Threat Intelligence Group, "Widespread Data Theft Targets Salesforce Instances via Salesloft Drift," 2025\.

\[8\] Fortinet PSIRT, "Analysis of Reported Credential Compromise of FortiGate Devices," June 19, 2026\.

\[9\] Klue, "An Update on the Recent Klue Security Incident," 2026\. https://klue.com/blog/an-update-on-recent-klue-security-incident

\[10\] Verizon, *2025 Data Breach Investigations Report* (DBIR), 18th edition. https://www.verizon.com/business/resources/Tea/reports/2025-dbir-data-breach-investigations-report.pdf

\[11\] GitGuardian, *The State of Secrets Sprawl 2026*. https://www.gitguardian.com/state-of-secrets-sprawl-report-2026

\[12\] IBM Security and Ponemon Institute, *Cost of a Data Breach Report 2025*, 2025\.

\[13\] National Institute of Standards and Technology, Special Publication 800-63B-4, "Digital Identity Guidelines: Authentication and Authenticator Management." https://csrc.nist.gov/pubs/sp/800/63/b/4/final

\[14\] National Institute of Standards and Technology, Special Publication 800-207, "Zero Trust Architecture." https://doi.org/10.6028/NIST.SP.800-207

\[15\] National Security Agency, *Zero Trust Implementation Guideline* (ZIG), Phase One, January 2026\. https://media.defense.gov/2026/Jan/30/2003868308/-1/-1/0/CTR\_ZIG\_PHASE\_ONE.PDF

\[16\] National Institute of Standards and Technology, Special Publication 800-57 Part 1 Revision 5, "Recommendation for Key Management: Part 1, General," https://doi.org/10.6028/NIST.SP.800-57pt1r5; and Special Publication 800-130, "A Framework for Designing Cryptographic Key Management Systems," https://doi.org/10.6028/NIST.SP.800-130

\[17\] GitGuardian, "Identity Infrastructure: Why Credentials Are the Layer Directories Don't Secure," July 14, 2026\. https://blog.gitguardian.com/identity-infrastructure/
