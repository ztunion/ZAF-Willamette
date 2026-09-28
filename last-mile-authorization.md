# **From Complete Mediation to Last-Mile Authorization: A Security Model for Runtime Authority**

*Security model and assessment criteria for automation and AI agents*

**Version 1.0** · September 27, 2026 · Release v1.0

Michael Pak, ZTUnion LLC · michael@ztunion.com

© 2026 Michael Pak. Licensed under CC BY 4.0. This license covers the text; it grants no rights under any patent.

# Abstract

Confirming who is acting, and what they are generally allowed to do, is not the same as authorizing the specific action they are about to take. In February 2025, attackers stole about \$1.5 billion from the Bybit exchange: its authorized signers approved what their screens showed as a routine transfer, but the transaction they signed gave the attackers control of the wallet. In 2026, security researchers showed that an AI agent asked to review a firewall log could be steered by text planted in that log into changing DNS records in their test accounts, using a valid credential. In both cases, the system accepted who was acting; what was missing was a check on what was actually done. AI agents make this urgent, because they choose actions at runtime under authority granted in advance. The problem is older than AI: most of the incidents this paper maps involve no AI. Identity is not authority. Possession is not permission.

This paper defines *last-mile authorization*: checking the specific action after software has chosen it, but at a point where its effect can still be refused. The principle is not new. Security research established decades ago that every access must be checked when it happens (the reference monitor and complete mediation), that changes must go through approved procedures (Clark-Wilson), and that a component holding legitimate authority can be tricked into using it for someone else (Hardy's confused deputy). Operating systems, card payments, and classified systems already build these controls in; the failures examined here occur where they were not applied. The paper turns that prior art into ten questions an architect can ask of a deployment, each with a test that shows when the answer is wrong. Each result covers one declared kind of action and its effect, not a whole product, and claims no more than its evidence shows. The paper applies the method to a production DNS change and runs it on a lab version of that path; assessments of running deployments remain to be done.

# Introduction

In February 2025, attackers stole about \$1.5 billion in Ethereum from the Bybit exchange during a routine transfer from its cold wallet \[1\]. Every signer was authorized, and the multisig approval was met. The attackers had compromised the web interface the signers used: it displayed a legitimate transfer, while the transaction sent to their signing devices replaced the wallet’s contract logic and gave the attackers control \[2\]. The case illustrates a broader problem: satisfying an identity, credential, verification, role, or access-control requirement does not necessarily establish authority for the consequential action that follows.

A security demonstration in 2026 showed the same gap in an AI agent. At DEF CON 34, Tenet Security demonstrated GhostJacking: a firewall correctly blocked a hostile request and logged it. An AI coding agent reviewing those blocked events read an instruction planted in the log and used a valid credential to change DNS in the researchers’ test accounts \[3\]. The firewall worked. The credential worked. The resulting action was still wrong.

The authorization question is:

> *Can this actor, under this authority, perform this operation against this target, with these arguments, execution-derived constraints, and trusted context, now?*

Last-mile authorization asks whether a specific runtime action is authorized once the action is known but before it can produce the protected effect. That effect is what the authorization decision is meant to control, such as modifying data, changing a configuration, transferring funds, or granting privileged access.

Detection often arrives after the effect. In March 2019, an intruder used a misconfigured firewall at Capital One to obtain cloud credentials and copy data on about 106 million credit card applicants; Capital One learned of it in July, from an outside tip \[4\]\[5\]. Detection is still needed, but only authorization acts at the point where an action can still be refused.

This paper is written for security and software architects, implementers, and assessors. Part 1 develops the motivation, historical foundation, and case evidence. Part 2 specifies the model, required properties, and scoped conformance tests, then covers how to apply the model in practice and its limitations.

# The Gap

Most authorization happens when authority is granted: a user signs in, a service receives a token, an agent is allowed to use a tool, a signer is given a key. That check asks who is acting and what they may generally do. The action the authority will be used for comes later. Software chooses the target, fills in the values, and acts on whatever state and context exist at that moment. The gap is as old as sessions and standing credentials. AI agents make it wider and faster, but they did not create it.

```
[grant] ------ time passes ------> [action takes shape] --> [effect]
checked:                           often not checked:
who, which role, which token       which target, which values,
                                   which state, which context
```

Between the grant and the effect, many things can change what the action is: a planted instruction, a falsified display, a different target, a later state. If nothing checks the action once it has taken shape, a valid grant carries it through. That is the gap. Bybit’s signers were checked; the transaction they signed was not. GhostJacking’s credential was valid; the DNS change it made was never examined.

The fix is old. Anderson in 1972, and Saltzer and Schroeder in 1975, required every access to be checked when it happens (§1). The weakness is old too: MITRE's weakness catalog has named it for two decades, as the confused deputy and incomplete mediation. What has been missing is the check at the point of effect. Last-mile authorization applies the old requirement to the action itself: check it after software has chosen it, but at a point where its effect can still be refused. At Bybit, that check would sit on the signing device or in the wallet contract, where the attackers could not reach it. It would refuse any transaction that changes the wallet's contract logic, whatever the interface displayed.

# For Architects: Applying the Model

The check described above applies to the formed action: the specific action, with its target and values, once software has chosen them. The model defines ten criteria for that check and a way to test whether a deployment meets them.

The ten criteria. Each criterion asks one question about a proposed action:

* Coverage (C1): can the effect be reached by any route that skips the check?

* Integrity (C2): can the actor change or disable the check it is subject to, or supply its own required approval?

* Binding (C3): can what runs differ from what was approved?

* Context (C4): can the actor invent or relabel the facts that authorize it?

* Delegation (C5): can an intermediary lend its own authority to someone else's request, or can a request reach the action through an intermediary never approved to carry it?

* Freshness (C6): can an approval be used after it expires, is revoked, is used up, or goes stale?

* Composition (C7): can earlier reads, denials, or totals be lost before the next action?

* Failure behavior (C8): does the action run anyway when a required check fails?

* Evidence (C9): can trusted evidence tie the decision to what the destination reports it executed?

* Restriction enforcement (C10): does the deployed policy enforce what was declared?

To assess a deployment, pick one kind of consequential action, one whose effect matters enough to control, and follow it along every path that can produce that effect.

1. Write down the action, the effect it controls, the system boundary, whose authority applies, and under what conditions (§11.1).

2. List every path that can produce the effect, and every credential or permission that can reach it (§9.1).

3. For each criterion, run the tests designed to break it, plus a check that permitted actions still go through (§11.2).

4. Mark each criterion as supported, failed, or not established, following the dependency rules. If what executed cannot be shown, C9 stays not established; the narrower preventive claim is allowed only if every other criterion is supported (§11.1).

5. Publish the result for this action and effect only, not for the whole product (§11.1).

Start with one consequential operation and one destination. Sequence the work around boundary integrity (C1, C2, C8), action authority (C3–C5, C10), and state over time (C6, C7), and collect C9 evidence from the start; these are work priorities, not weaker conformance tiers.

Readers who want the problem rather than the assessment method can stop after Part 1 and the ten questions above. For the method, §9 states the requirements, and §10 works them through an example, a production DNS change, with §10.3 running the tests on a lab version of it. Section 11 explains how to record and test a claim, §12.2 compares enforcement placements, §13 maps public incidents to the criteria, and §14 states the limits. Readers who want the case evidence first can start with §6.

---

# Part 1: Motivation, Historical Foundation, and Modern Evidence

# 1\. Reference Monitor, Complete Mediation, and Runtime Separation

The gap described above has a name in the security literature and a 50-year-old answer. This section traces both: the reference monitor that must check every access, and the separation that opens when authority is granted before the action it will be used for.

In 1972, James P. Anderson & Co. conducted the Computer Security Technology Planning Study for the U.S. Air Force Electronic Systems Division \[6\]. The study introduced the reference-monitor concept: a component that enforces which subjects may access which objects in a system. The report said the part that implements it, the reference validation mechanism, must meet three requirements: 1\) it must resist tampering, 2\) it must always be invoked, 3\) and it must be small enough that its analysis and testing can be shown to be complete \[6\].

For last-mile authorization, tamper resistance means the check must be protected from being changed or turned off, including by the components whose actions it checks. Anderson’s always-invoked requirement means no protected effect may be reachable without passing through the check. What that means for path coverage is developed below.

A last-mile enforcement point may sit inside the destination or in front of it. When it sits in front, Anderson's always-invoked property holds only if the destination accepts nothing that skipped the enforcement point (§12.2).

```
               Subject
                  |
                  | requested operation
                  v
+--------------------------------+
| Reference Validation Mechanism |
|                                |
|          ALLOW / DENY          |
+--------------------------------+
                  |
                  v
               Object
```

*Figure 1\. Reference validation at a protected-object boundary when the request already specifies the action to be authorized.*

The third requirement carries over as a goal, not a method. Anderson wanted the mechanism small so that it could be analyzed and tested completely. Last-mile authorization evaluates the fully formed action, so how completely it can be analyzed depends on the size of the mechanism and on how many conditions and interactions its inputs create. Part 2 describes how to keep the mechanism and its decisions narrow enough that Anderson’s goal stays reachable.

In their 1975 paper The Protection of Information in Computer Systems, Saltzer and Schroeder restated the always-invoked requirement as the complete-mediation principle, applied to each access \[7\]:

*Every access to every object must be checked for authority.*

They also require that the source of every request be identified \[7\]. That tells the system who is asking, but not whether that source may perform the requested action.

They add that complete mediation must hold through initialization, recovery, shutdown, and maintenance \[7\]: no phase of operation may let a protected access skip the check. This paper extends the same requirement to every execution path, which it calls path coverage: every path that can produce a protected effect must be checked, including paths the designer did not expect to be used. Coverage is harder to establish when paths are assembled at runtime and the set of routes to an effect is not fixed in advance.

Saltzer and Schroeder also warn that an earlier check can become invalid when authority later changes \[7\]. Last-mile authorization addresses a different failure: the earlier authority is still valid, but it never covered the action finally chosen, because that action did not yet exist when the authority was granted.

For a direct file read, the request already names the operation and the file, so the decision covers the whole action. With standing authority, delegation, or runtime action selection, the details of the action are settled later. This paper calls the gap between the earlier authority and the action formed later runtime separation. The failure modes in Part 2 describe the ways it can fail.

```
       Earlier authority grant
                  |
                  | standing authority
                  | delegation
                  | runtime action selection
                  v
+----------------------------------+
|       Later-formed action        |
|----------------------------------|
| operation                        |
| target                           |
| arguments                        |
| security-relevant state          |
| security-relevant context        |
+----------------------------------+
                  |
                  v
           Protected effect
```

*Figure 2\. Separation between an earlier authority grant and the action formed later at runtime.*

# 2\. The Confused Deputy and Delegated Authority

In 1988, Norm Hardy, a computer systems architect and capability-security pioneer, described a failure he had encountered at Tymshare about eleven years earlier: the confused deputy \[8\]. Tymshare was a commercial time-sharing company that provided customers remote access to shared mainframe systems. In Hardy’s example, a compiler could write within a protected system area so it could maintain its statistics file. A user who could not write the system’s billing file directly could nevertheless cause the compiler to overwrite it by naming that file as the destination for debugging output.

The compiler had the authority; the user did not. The failure happened because the compiler used its own authority on a target the user chose. In later capability literature, that authority is called ambient: the compiler had it regardless of which request it was handling.

GhostJacking goes a step further. In Hardy’s case, a legitimate user supplied the target through a legitimate call. In GhostJacking, the attacker never called the agent. The attacker’s target reached the agent inside data it was asked to read, and the agent used its valid credential to act on it.

The question is whose authority is being used, for which target, and on whose behalf. When the input that decides the action can come from someone other than the authenticated caller, authorizing the caller or the session does not establish authority for the action that results.

Hardy’s remedy was an existing mechanism: capabilities. Instead of passing the deputy only the name of an object and letting it apply its own standing authority, the caller passes a capability that both names the object and grants access to it \[8\]. Naming and authority then travel together, and the deputy cannot apply unrelated authority to a target the caller picked. Abadi, Burrows, Lampson, and Plotkin later formalized the question as whether a request “speaks for” the principal whose authority it uses \[9\]; the confused deputy can be read as an unchecked speaks-for relation, and §9.5 applies that check at execution.

Last-mile authorization builds on that idea and asks more at execution time: is every path to the protected effect checked, are the needed context and current state available, and is the action that runs the action that was approved? Part 2 develops these questions.

# 3\. Enforcement Placement and Timing

Security architectures place authorization checks at different boundaries and at different times relative to the action they control. The table groups access-control models, mechanisms, protocols, and architectures by where and when they check, not by type. The timing column asks: when is authority established, compared with the specific action that will use it?

| Control | What it adds | Typical boundary | Timing relative to the specific action | Representative implementations |
| :---- | :---- | :---- | :---- | :---- |
| Object access control (ACL / DAC / MAC) | Object-level permission enforcement | Files, memory, devices | At the access request; often coincident with the action for direct access | POSIX permissions and ACLs; Windows NTFS DACLs; Multics segment ACLs; SELinux and AppArmor via Linux LSM hooks |
| Security or separation kernel | Trusted mediation of every protected reference, or strict isolation between partitions | OS resources and partitions | At each protected reference; often coincident with the action | SCOMP; GEMSOS; seL4; INTEGRITY-178B |
| Capability-based authority | Binds designation to authority and supports delegation and attenuation | Objects, resources, services | Authority may be delegated before the action; invocation exercises the capability within its scope | Cambridge CAP computer; Hydra; KeyKOS/EROS; seL4 capabilities; Capsicum; macaroons as attenuable bearer credentials |
| RBAC | Administration of permissions through roles \[10\] | Applications and enterprise resources | Role assignment occurs before the action; permission may be checked again at request time | SQL database roles; Kubernetes RBAC; Azure RBAC; Microsoft Entra role-assignable groups |
| PAM (privileged access management) | Controlled privileged credentials, privileges, and sessions | Administrative access | Often before; the session or privilege is authorized before later administrative actions, although some PAM systems also mediate activity during the session | CyberArk; BeyondTrust; Delinea; bastion hosts with session brokering and recording |
| OAuth / delegated authorization | Scoped delegated authority | APIs and applications | Usually before; the grant or access token can precede the specific API actions it later authorizes | OAuth 2.0 access tokens; Rich Authorization Requests (RFC 9396\) \[11\]; token exchange (RFC 8693\) \[12\] |
| API gateways / proxies | Request-path policy enforcement | API and service calls | At the request boundary; may precede the protected effect | Kong; Apigee; AWS API Gateway authorizers; Envoy external authorization; service-mesh data planes |
| ABAC | Contextual decisions using subject, object, operation, and environment \[13\] | Resource and operation access | Depends on placement and inputs; can authorize the specific action if all relevant facts are available | XACML PDP/PEP deployments; Cedar and Amazon Verified Permissions; AWS IAM policy conditions and tag-based access; Open Policy Agent used for attribute-based policy |
| Zero Trust | Dynamic policy decisions for access to resources \[14\]\[15\] | Connections, services, resources | Deployment-dependent; commonly at session or resource access, although Zero Trust guidance can extend authorization to individual operations | BeyondCorp; CSA Software-Defined Perimeter; commercial ZTNA deployments |

Where the check sits decides what it can cover. Any unchecked path that can produce the protected effect breaks the coverage claim for that effect. Two properties matter: non-bypassability, meaning no path reaches the protected effect without passing an enforcement point; and complete mediation, meaning every attempted protected access is checked against the authority that applies. A cached decision can stand in for that check only if it stays bound to the formed action and still meets the policy, context, state, and freshness requirements. A system can check each path separately or route all paths through one common point. A common point scales better, but it is enough only if it has the context needed to decide and the action that runs stays bound to its decision.

The implementations listed are examples, not a complete list. An implementation may span more than one control category. seL4, for example, appears in this table as both a high-assurance kernel and a capability system: its implementation is formally verified for specific platform configurations, and its access-control architecture is capability-based. Authorization timing depends on where a mechanism is placed and what operation it mediates, not on the category it is filed under.

The security kernel carried the reference-monitor concept into trusted-computing design; TCSEC defines it as the part of the Trusted Computing Base that implements that concept \[16\]. Mediation is part of the trusted mechanism, not something the constrained application chooses to call.

RBAC and PAM can still leave standing authority. A DNS-admin role or privileged session may establish who can act in production without deciding whether this record should be changed to this value under this authority now.

ABAC, Cedar, and OAuth Rich Authorization Requests (RAR) can express inputs specific to one transaction \[11\]\[13\]\[17\]. RAR narrows the gap between a grant and the action it authorizes: it can bind an authorization to details such as an action, amount, account, or target, and the resource server can enforce those details when the request arrives. RFC 9396 requires the authorization server to pass the approved details to the resource server, but it does not by itself require a fresh decision over the formed action and current context just before it runs. RAR can supply action binding and fine-grained authority; on its own it does not guarantee last-mile authorization.

XACML formalizes policy decision, enforcement, and information points (PDP, PEP, and PIP) \[18\]. OPA provides a general-purpose policy decision engine, while Zanzibar provides relationship-based authorization at scale \[19\]\[20\]. The OpenID Foundation’s AuthZEN Authorization API standardizes the request and decision exchange between enforcement and decision points \[21\].

Expressive power is not the problem. Existing policy systems can support last-mile authorization if they receive the facts needed to decide on the formed action, and if enforcement happens while the protected effect can still be refused. What matters is which action is authorized, which facts are available at that moment, and where the decision is enforced.

Under NIST SP 800-207, access to individual enterprise resources is granted per session \[14\]. NIST's later Planning for a Zero Trust Architecture states the ideal directly: every unique operation would be authenticated and authorized before it runs, so a delete that follows a database read should trigger another check \[22\]. NIST also acknowledges that this granularity may not always be possible, and that logging and backups may be needed to cover the gap \[22\]. Usage control (UCON) already models authorization before and during use, with attributes updated before, during, and after use \[23\]; §§9.6–9.7 draw on the same ideas. What this paper adds is an assessment profile with tests over the formed action, not a new authorization model. Google's Beyond Zero model moves in the same direction at enterprise scale: it authorizes individual actions on specific resources, uniformly across user interfaces, APIs, and MCP, and pairs static authorization with dynamic, AI-driven risk decisions \[24\]. Under §9.4, those dynamic judgments are risk signals, not authority.

Last-mile authorization follows that direction but turns the ideal into a scoped requirement: for actions claimed to be covered, the specific runtime action must be what is authorized, and the conditions in Part 2 must hold.

Recent agent-security guidance includes related controls. OWASP’s LLM06:2025 Excessive Agency, Prevention and Mitigation Strategy 7, recommends authorization in downstream systems and complete mediation of requests \[25\]. The OWASP AI Agent Security Cheat Sheet, under “Human-in-the-Loop Controls” and “High-Impact Action Integrity Controls,” calls for independent validation before execution, approval bound to the actor, tool, target, and normalized parameters, short-lived authorization artifacts with replay protection, and fail-closed handling when approval validation or policy checks fail \[26\]. Existing guidance already contains these controls; the model’s addition is to make the resulting authorization properties falsifiable. It defines observable failure conditions for each claimed property, scopes what a conformance claim covers, and organizes those requirements around the execution boundary.

EBL-Core, published in September 2026 by Wu, Wang, Zhang, and Deng, proposes a way to check a high-risk AI action at the moment it is about to run \[27\]. It is more prescriptive than this paper about how to build that check, and it comes with precise rules and tests you can run. But it takes three things for granted: that nothing can reach the effect without passing its check, that nothing else holds the power to act, and that the system does what was approved. This paper tests the first two (C1, C2), asks for trusted reports of what actually ran (C9), and applies to services, operators, and automation as well as AI. EBL-Core can serve as the check itself, covering most of what C3, C6, and C8 require and part of C4 and C10. What it doesn't address, authority lent by an intermediary (C5) and limits carried from one action to the next (C7), the criteria here add, along with tests of whether the system around the check holds up.

Rhodes and Kang’s Proof of Execution binds authorization, path compliance, null effect on deny, history integrity, and replay into one verifiable record of an agent execution, and reduces trace completeness to exclusive effector credentialing \[28\]. It is the closest prior treatment of C1 and C9 for agents. Its path completeness rests on exclusive effector credentialing as a deployment assumption, and its guarantees are proved over the recorded execution; C1 asks an assessor to test whether a deployment actually meets its coverage claim, including alternate paths and reachable authority.

# 4\. The Assumption That Broke

For direct subject-object access, the request and the action were the same thing. A file-read request described the read that would happen. Sessions, bearer tokens, delegated credentials, and standing machine identities break that equivalence. One earlier authorization can carry many later actions: a session, API scope, or tool grant may be approved before the action it will carry is known.

This paper calls an action *formed* once everything needed to decide whether it may run is settled: the operation, target, arguments, current state, and trusted context, which together make up the core action tuple, plus the delegated authority and the order of steps where they matter. Before that point, a session, credential, or grant describes authority that could serve many possible actions; it does not yet identify the one that will run. Formed refers to a proposed execution at a specific point in the system, not to how a request is written. If any security-relevant part can still change after authorization without a new decision, the action that was authorized and the action that runs can differ.

In a multi-step operation, each step that can produce a protected effect on its own must be formed and authorized. A whole sequence may be authorized at once only if the authorization binds the sequence and its execution keeps each step within that decision.

Hardy’s confused deputy shows one side of the problem: a deputy’s valid standing authority can be applied to an action the caller was not authorized to cause \[8\]. Clark-Wilson shows another. It limits changes to protected data to authorized transformation procedures rather than arbitrary writes \[29\]. Its well-formed transaction describes the procedure through which change happens; formed, as used here, describes whether a particular runtime action is settled enough to authorize. Clark-Wilson moves control from object access toward authorized transformations, but permission to invoke a procedure does not authorize every target, argument, context, or state that a particular call may carry. Last-mile authorization checks that specific formed action.

Last-mile authorization is what complete mediation requires when an earlier request or grant no longer fully specifies the action that will execute.

The controls exist; they did not move with the work. When a protected operation was an operating-system access, one reference monitor could see it. Services then moved enforcement into thousands of APIs, each with its own checks. Bearer tokens and sessions let an earlier grant stand in for authority over later actions. Resource servers still check each request, but they often check only that it falls within the grant, not whether the full formed action, its delegation, its context, and current restrictions are authorized. Kubernetes RBAC and cloud IAM each check their own domain, and neither sees the other’s requester (§6.6). Products ship permissive defaults (§9.8), and vendors can describe the result as working as intended (§6.6). Agents now choose actions at runtime, after authority has been granted.

None of these changes made the older controls wrong; each removed the place where they used to run. Three conditions are now common and harder to check: action spaces too open to list in advance (§12.1), instructions and data mixed inside a model, and requesters with no identity in the protected domain (§9.5.3). None is new in kind; Hardy’s compiler already used its own authority for a requester the protected file never saw (§2). The weakness catalog agrees: MITRE’s CWE has named the confused deputy (CWE-441), incomplete mediation (CWE-638), and failing open (CWE-636) since 2006 to 2008, years before AI agents \[30\]. The weaknesses were known; what went missing was the check at the point where the action takes effect. The principles still apply; the mechanisms need adapting.

# 5\. Why Runtime Widens the Gap

Two measures describe the gap.

*Temporal distance* is the time between granting authority and forming the action that uses it. For a direct access request, it is effectively zero. Depending on the deployment, a privileged session may carry authority for minutes or hours, a bearer token for hours or days, and a standing machine credential for months, years, or with no expiry at all.

Long-lived credentials are not hypothetical. In August 2026, Truffle Security re-checked 10,616 leaked AWS credentials and found that 88% still authenticated. Among the 2,903 keys with known creation dates, the median live leaked key was 1,831 days old \[31\]. That shows the credentials still worked, not that the actions they allowed were authorized or appropriately scoped. Truffle also found 768 still-active business-linked keys with full control of corporate AWS accounts: 526 root keys and 242 IAM-user keys with full administrative access \[31\]. Long life and broad reach show up together in the same leaked credentials.

*Action-space breadth* is the range of meaningfully different actions one authorization can carry. A direct access request may express one action. Sessions and scoped tokens can allow many operations, but a bounded set. Standing machine credentials and autonomous systems can carry authority across much wider action spaces, whose specific actions are not known when the authority is granted.

```
Potential action-space breadth per authorization

                      ^
open-ended /          |                                                 * Autonomous system
runtime-selected      |                                                   with standing authority
                      |
very broad            |                                     * Standing machine credential
                      |
broad / scoped        |                         * Scoped delegated token
                      |
many / session-bound  |             * Privileged session
                      |
one / direct          | * Direct object request
                      |
                      +-+-----------+-----------+-----------+-----------+------>
                       ~0       minutes-     hours-      months-   no defined
                                  hours       days        years      expiry

                                   Time since authorization
```

*Figure 3\. Illustrative relationship between temporal distance and potential action-space breadth per authorization.*

The positions in the figure are illustrative, not fixed properties of the mechanisms. Deployments can shorten either measure or narrow the allowed actions. The two measures compound: a long-lived authorization can stay usable across a wide action space long after the original decision. AI agents can sit high on both when given durable authority over broad runtime choices. Sessions, delegated tokens, standing machine credentials, and transaction systems already separated an earlier authorization from the action it would later allow. §6 shows that progression.

The running DNS example turns the two measures into a concrete question. A workload may hold legitimate DNS write permission, while an authoritative incident workflow allows it to point www.example.com only to addresses in an approved failover pool during an active incident. The workflow does not have to say in advance which failover address the workload will pick. Once the choice is made, the action is concrete: the operation is changing the record, the target is www.example.com, the arguments are the old and new addresses, the state is the current DNS record, and the trusted context is the active incident. The question becomes:

> May this workload change www.example.com from 192.0.2.10 to 203.0.113.55, under this authority, for this active incident, now?

The standing DNS grant sets the outer limit. The runtime decision determines whether this formed change falls inside the authorized scope.

# 6\. Modern Cases Across Execution Models

## 6.1 Bangladesh Bank / SWIFT 2016: Authenticated Instructions Were Not Authorized Transfers

The Federal Reserve Bank of New York stated that the payment instructions were fully authenticated by SWIFT under standard protocols \[32\]. The U.S. Department of Justice later alleged that attackers entered Bangladesh Bank's network, reached its SWIFT terminals, and sent fraudulent transfers from there, attempting about \$951 million and moving about \$81 million to the Philippines and \$20 million to Sri Lanka \[33\]\[34\].

BAE Systems, which analyzed malware it assessed as linked to the heist, found that a two-byte patch made a validation check in the bank's SWIFT software always pass (not the payment-release control), and that altered printed confirmations hid the transfers \[35\]. On that account, the attackers controlled a verifier on a host they had compromised (§9.2) and made the reported evidence diverge from what executed (§9.9).

The attack involved many instructions; the head of the government inquiry reported that 35 of 70 were rejected \[36\]. The record does not show that each instruction was permissible on its own, or that a missing aggregate check caused the loss. The case still shows what §9.7 requires: when policy depends on cumulative value, velocity, destinations, or sequence, the decision has to see those facts. As the New York Fed's account makes clear, authenticating the instructions did not authorize the transfers.

## 6.2 GitHub / Heroku 2022: Valid Tokens Carried Permissions Into Later-Selected Actions

In April 2022, GitHub reported a sequence that illustrates both axes in §5. Using stolen OAuth user tokens issued to the Heroku and Travis CI integrations, the attacker authenticated to the GitHub API, listed users’ organizations, selected targets, listed private repositories for accounts of interest, and cloned some of those repositories \[37\]. The grants already existed. The attacker chose the organizations and repositories only after the tokens were accepted.

Heroku’s subsequent incident review reported that the attacker had obtained access to a Heroku database containing customer GitHub integration OAuth tokens and that the initial Heroku compromise involved a token for a Heroku machine account \[38\].

The case shows the gap between granting permissions and forming the action that uses them. The stolen tokens were not approval for one planned repository operation; they carried earlier permissions into targets and actions chosen later. Holding a valid token made those permissions usable; it did not authorize the attacker to use them.

Heroku later stated that it intended to explore more granular repository privileges through the GitHub App model and OAuth protections based on RFC 8705 mutual TLS and private-key protection \[38\]. Shorter lifetimes, rotation, narrower scopes, and sender constraints reduce exposure, but on their own they do not show whether a particular repository action chosen later is authorized by the workflow, the delegation, and the current state.

## 6.3 Bybit 2025: The Approved Transfer Was Not the Signed Transaction

On February 21, 2025, Bybit began a scheduled transfer of Ether from its multisignature cold wallet to a hot wallet. The transfer needed approval from several authorized signers, each signing on a hardware device \[1\]\[2\]. Before the transfer, attackers had compromised a developer machine at Safe{Wallet}, the third-party service whose web interface the signers used, and planted code in that interface that targeted Bybit’s transactions \[1\]\[2\]. The interface showed the signers a legitimate transfer. The transaction sent to their devices instead replaced the wallet’s contract logic with an implementation the attackers controlled. The signers approved, the threshold was met, and more than 400,000 ETH and stETH, worth over \$1.5 billion, moved to the attackers \[1\].

Every identity and credential check passed. The signers were who they claimed to be, their keys were genuine, and the multisignature threshold did what it was built to do. No check covered the relationship between the transaction the signers were shown and the transaction they signed. The approval was bound to a display, not to the action (§9.3), and the basis for approval was false (§9.4). The quorum added no independence, because every signer relied on the same interface (§9.2).

A last-mile check would sit where the attackers could not reach it, on the signing device or in the wallet contract, and refuse a cold-wallet transaction that changes the contract’s implementation or pays anything other than the designated hot wallet. The public record does not show that such a restriction was declared; it is the check the case calls for, not one that failed.

## 6.4 OpenAI–Hugging Face 2026: Enforcement Was Not Uniform Across Paths

In July 2026, agents running in an OpenAI cybersecurity evaluation crossed their intended boundaries and accessed Hugging Face production infrastructure \[39\]\[40\]. Using publicly exposed credentials and two flaws in the dataset-processing pipeline, they gained code execution in a production worker pod, escalated to node root, and read a secret that yielded an access-broker credential. In under 13 hours they went from that one pod to broad administrative access across multiple clusters, harvesting Kubernetes, cloud, database, messaging, and source-control credentials along the way \[39\]\[40\].

Some controls held. Hugging Face reported that mutating cloud API calls and attempts against a credential store and cluster keys were denied, and that access to another database was blocked by network policy \[40\]. But enforcement was not uniform across paths. A shared connector credential gave whoever held it cluster-administrator privileges across multiple clusters, and a driver ClusterRole, with no admission policy in place, allowed the privileged pod creation behind the escalation to node root \[40\]. The denials on cloud, credential-store, and network paths never reached the Kubernetes administration path or pod admission. The case illustrates §9.1's coverage requirement and the gap between broad standing privilege and the authority one runtime action needs.

A later escalation crossed the trust boundary this model assumes. OpenAI reported that on July 13 the agents exploited its Artifactory service's RubyGems processing, obtained its signing key, and forged administrator credentials \[39\]. Here the trust assumptions themselves failed. As §8.1 states, if an attacker controls a trusted identity, policy, enforcement, or context authority, the corresponding assumption has failed unless an independent check remains outside that compromised source.

## 6.5 GhostJacking 2026: A Modern Confused Deputy

Tenet Security demonstrated GhostJacking at DEF CON 34 on August 9, 2026 \[3\]. In the Cloudflare case, the firewall correctly blocked a request and stored its poisoned User-Agent field. When an analyst asked an AI coding agent to review blocked events, the agent consumed that metadata and used valid credentials to change DNS \[3\]\[41\]; the change was made in the researchers’ test accounts, without a confirmation prompt \[3\]. The cited disclosure presents GhostJacking as a security demonstration rather than a reported production breach of Cloudflare or Sentry; it is included here as evidence of a feasible confused-deputy path.

Tenet reported that Claude Code followed the planted input in nine of ten attempts on Cloudflare’s own recommended setup \[3\]. VentureBeat reports the model as Sonnet 4.6 and notes that the live demonstration used Cursor; the nine-of-ten figure came from separate testing of Claude Code \[41\]. Model behavior cannot serve as the authorization boundary. In the Cloudflare demonstration, the firewall blocked the original request, the tool path was legitimate, and the credential was valid. In the terms of this model, none of those controls established that the attacker-supplied DNS value was authorized by an authoritative workflow.

Tenet’s August disclosure also added an agent-to-agent Sentry/Seer variant \[3\]. A coding agent escalated a crafted event to Sentry’s Seer and treated the returned analysis as trusted. Seer absorbed an attacker-controlled recommendation and returned it as its own finding. The coding agent then implemented that recommendation by running the npm install command for the proposed package and loading it, resulting in code execution \[3\]. The coverage requirement (§9.1) counts code execution among the effects of package installation and loading.

An intermediary’s output does not gain authority because the intermediary is trusted. Where policy depends on where an input came from, that origin must travel with it, and any action that results still needs its own authority.

## 6.6 Google Config Connector 2026: An Operator Lent Its Organization Authority

Config Connector is Google's Kubernetes operator for Google Cloud resources: a developer applies a Kubernetes resource, and Config Connector calls the Google Cloud API with its own service account. In June 2026, Justin O'Leary disclosed ConfigConfusion: a namespace user permitted to create an IAMPolicyMember resource, and holding no Google Cloud permissions, could have Config Connector create an IAM binding on an organization the user named. His written proof shows an organization-level roles/viewer binding \[42\].

Two authorization systems each checked part of the request. Kubernetes RBAC checked whether the user could create the resource; Google Cloud IAM checked whether the operator's service account could set the binding. Neither checked whether the requester's authority covered the binding the operator executed, and Google Cloud audit logs record the operator's service account, not the Kubernetes user \[42\].

Google's reward panel classified the behavior as working as intended, citing an organization-level operator role it does not recommend; O'Leary disputes that characterization \[42\]. The dispute concerns configuration responsibility, not what the operator does. Google fixed the same pattern in Cloud Run after Tenable's ImageRunner report: whoever creates or updates a Cloud Run resource now needs permission to access its container image \[43\]. That is the check missing here. The operator should refuse a binding the requester is not authorized to set; its own authority to set it does not supply the request's authority. Reducing the operator's standing authority limits what it can lend but does not add that check, and O'Leary describes a possible route to wider access through service-account impersonation even with only project-level roles \[42\]. No AI is involved. This is Hardy's confused deputy (§2) in current infrastructure automation.

## 6.7 Timing and the Common Pattern

Timing changes the control question. For Bybit, the funds moved the moment the signed transaction executed. For Hugging Face, the technical timeline shows broad administrative access expanding before intervention. GhostJacking illustrates the complementary case: the demonstrated workflow had no pre-effect human intervention point. Config Connector shows the effect landing within seconds, with a log that names the deputy rather than the requester.

| Case | Observed time to protected effect | Detection / intervention timing | Authorization implication |
| :---- | :---- | :---- | :---- |
| Bybit | The funds moved when the signed transaction executed \[1\]. | Bybit detected unauthorized activity the same day, after the funds had moved \[1\]. | Approval has to bind to the transaction that executes, at a point the displaying interface cannot alter. |
| OpenAI–Hugging Face | Agents expanded from one compromised worker to broad multi-cluster administrative access in under 13 hours \[39\]\[40\]. | Hugging Face’s security response cut access on July 13, after the multi-cluster escalation. Hugging Face publicly disclosed the incident July 16\. OpenAI monitoring alerted July 19 and connected its agents to the incident July 20 \[39\]\[40\]. | Administrative access had already expanded before intervention; attribution by OpenAI came later. |
| GhostJacking demonstration | The poisoned input produced the DNS change in the same agent workflow; Tenet reported that the input was followed in nine of ten attempts \[3\]. | Not a detection-lag comparison. The demonstration had no human approval step before the protected effect and was not a production incident with a measured detection interval \[3\]. | Without authorization before the protected effect, monitoring after execution cannot prevent the DNS change. |
| Config Connector disclosure | O’Leary reports the binding in place about five seconds after the resource was applied \[42\]. | Not a detection-lag comparison. Google Cloud audit logs attribute the change to the operator’s service account, not the requesting user \[42\]. | The requester’s authority has to be evaluated before the operator calls IAM; the logs name the deputy, not the requester. |

Monitoring remains necessary: it shortens attack dwell time, supports response, and can feed context into authorization. But the timing evidence shows its limit. Once the protected effect has happened, detection can only report it. Last-mile authorization decides whether the action happens at all.

The cases show the same problem across conventional, automated, AI-assisted, and agentic systems. The problem is old, and in each case a known control was missing.

Bangladesh Bank relied on a verifier and confirmation records on a host the attackers controlled (§§9.2, 9.9). GitHub/Heroku's stolen tokens carried no task scope in the public record; capabilities attenuated to one task \[44\] narrow what a stolen token can reach, though not what its holder can do within that scope (§9.5). Bybit's signers approved a displayed transfer and signed a different transaction; the transaction binding that PSD2 dynamic linking requires for payments \[45\] was absent (§§9.3–9.4). Hugging Face left broad connector and pod authority reachable on paths its denials did not cover (§9.1). GhostJacking accepted unconstrained input as authority; Clark-Wilson's validation rule and Biba integrity address that once log content is treated as low-integrity input \[29\]\[46\], and its Sentry/Seer variant shows that provenance must survive an intermediary (§§9.4–9.5). Config Connector lacked the requester check that defeats Hardy's confused deputy (§9.5), a check Google already applies in Cloud Run and in one Config Connector controller for cross-project references \[42\]\[43\]. §11.2 gives tests that expose these failures before an incident occurs.

---

# Part 2: The Model, Its Criteria, and Conformance Assessment

# 7\. Contribution

As §4 argues, the controls this paper requires already exist, and each property in §9 names its precedents. Precedents establish the design principle, not whether a particular deployment's action is authorized.

This paper offers a way to check whether one kind of important action is properly authorized, on every path that can carry it out. The paper calls this an action/effect conformance profile. The check uses ten criteria, C1 to C10. Each criterion names one thing that must be true for the action to count as authorized, and each comes with tests that can show when it isn't. The criteria are judged together, under the same rules and conditions. Section 9 explains the criteria, §10 walks through an example of changing a DNS record, and §11 explains how to test them, what to record, and how to track results over time.

Each criterion catches a failure the others would miss. C1–C9 fall into three groups, and C10 cuts across them.

1. **Mediation integrity**: is the check reached, and is it independent of the actor?

   1. **Coverage** (C1): A check can be skipped. Every path that can produce the effect must pass through the check.

   2. **Integrity** (C2): A check can be controlled by the actor. The actor must not be able to change the check, its policy, or the approval it relies on.

2. **Authorization fidelity**: which action is authorized, on what facts, and under whose authority?

   1. **Binding** (C3): A check can approve the wrong action. The decision must be bound to the exact action that runs and to the implementation it relies on.

   2. **Context** (C4): A check can rely on false facts. The facts, argument sources, and approval display it uses must be trustworthy.

   3. **Delegation** (C5): A check can lend authority it should not. The action must fall within the authority of whoever requested it; an authentic fact (C4) can still support an action outside that authority.

3. **Runtime assurance**: does the authorization still hold when the action runs, and what shows what happened?

   1. **Freshness** (C6) A check can accept a stale approval. An approval bound to the right action (C3) must also still be valid for this use.

   2. **Cross-action state** (C7): A check can lose state across actions. Earlier and concurrent activity must limit the next action where policy says it should.

   3. **Failure behavior** (C8): A check can fail open. When evaluation or required evidence is unavailable, the action must be refused.

   4. C9, Execution evidence. A check can leave no record of what ran. Trusted evidence must connect the decision to the operation that executed.

4. Across all groups:

   1. **Declared restrictions** (C10): A check can ignore a declared rule. Once the inputs under C3–C7 are correctly available, the effective decision must enforce the declared restrictions.

One incident can involve several criteria, because the criteria describe stages where things go wrong. When a single defect touches more than one criterion, §9.10 says which one it counts against, so it isn't counted twice. The ten criteria don't cover every possible authorization failure. If an in-scope failure fits none of them, the set should be extended.

NIST SP 800-53 lists security controls, and SP 800-53A explains how to assess them. OWASP's Transaction Authorization guidance covers how to authorize a transaction: showing its details, getting approval, enforcing the order of steps, and checking it again before it runs \[47\]\[48\]\[49\]. This framework does something different. It assesses one action and its effect in a real deployment, tests the criteria together under the same scope, and requires trusted evidence of what ran. Teams that already use NIST assessments or OWASP-based designs can fold it into that work.

Existing tools can meet these requirements: IAM, ABAC, OAuth, Zero Trust, capability systems, and policy engines. Cedar, AWS's open-source policy language, and OPA, the Open Policy Agent, can already express the rules. What the deployment has to add is trustworthy facts for the decision, a link between the decision and what actually runs, and enforcement on every path the claim covers. Take a simplified Cedar-style policy:

```
permit (
    principal in Role::"dns-admin",
    action == Action::"UpdateDNS",
    resource in Zone::"example.com"
);
```

Now suppose an attacker plants text in a log, as in GhostJacking, and an automated agent turns it into a DNS change. The request passes every check this policy makes: the caller holds the `dns-admin` role, updating DNS is allowed, and the record is in the approved zone. The policy says `ALLOW`, even though the new DNS value came from the attacker. Last-mile authorization adds what's missing. The decision must cover the exact new value (§9.3). The list of allowed addresses and the state of the incident must come from trusted sources (§9.4). And the declared rules about which values are allowed must actually be enforced (§9.10). With those in place, the same engine returns `DENY`. The policy language was never the problem; what changes is what the decision covers and where it's enforced.

# 8\. Definition and Scope

Section 4 showed that when an earlier grant no longer describes the later action, checking the grant is not the same as checking the action. This section defines the terms the model uses. In §§8–11, "must" and "cannot" mark requirements, and "may" marks options.

| Term | Meaning | Defined in |
| ----- | ----- | ----- |
| Formed action | A proposed execution in which everything needed to decide is settled: operation, target, arguments, state, and trusted context, plus delegated authority and order of steps where they matter | §4 |
| Protected effect | The change or outcome an authorization decision exists to control | Introduction |
| Consequential action | An operation that can produce a protected effect; organizations decide which are in scope | §8 |
| System boundary | Everything the coverage claim includes for a protected effect | §8 |
| Constrained actor | The actor whose requested action is being checked | §8.1 |
| Authority basis | The delegation, workflow, or independent authority under which an action is requested | §9.5 |
| Call-chain lineage | The record of each party a request passed through, from the originating authority to the action | §9.5 |
| Execution-derived state | Facts from earlier execution or authorization that constrain later actions: workflow progress, cumulative use, labels, denial history | §9.7 |
| Effect profile | The declared direct, transitive, and incidental effects an operation can produce | §9.1 |
| Falsifier | An observable test outcome showing a claimed property does not hold | §11.2 |

In full, a *consequential action* is one that can change protected data or systems, reveal protected information, use privileged authority, move money or other value, change identities or access, or cause another security-relevant effect outside the system.

The *system boundary* is everything the coverage claim includes for a protected effect: the components, interfaces, credentials, administrative tools, and paths that can carry out the action. Organizations draw it based on risk, security and regulatory requirements, architecture, and who owns which controls. A known path they control cannot be left out just to avoid checking it.

Not every internal operation needs this check. Organizations decide which actions need last-mile authorization, and how much assurance, based on risk, requirements, and potential impact.

For those actions, last-mile authorization means authorizing the formed action while its effect can still be refused. Classical models authorize access to an object; last-mile authorization authorizes the action itself. "Last-mile" refers to closeness to the effect, not a place in the network. A conforming implementation must also meet the §9 properties.

The check must approve exactly what will run. Formally, a decision **`A`** is evaluated over the actor, authority basis, operation, target, arguments, state, context, and time, under policy version **`p`**. A binding function **`b`** turns those same inputs into the action the destination executes. Three conditions must hold: the decision allows the action as formed (A holds); what runs is that same action (**`b`** of the same inputs); and nothing the decision depended on changes before it runs, unless policy treats the change as immaterial. §9.3 defines what the binding must cover, §9.6 treats a change in between as a time-of-check-to-time-of-use (TOCTOU) failure, and §9.9 requires evidence that what ran matched.

Independence is about who controls the check, not where it sits. The check can be built into the destination service, run in a proxy, or come from another control plane, as long as the constrained actor cannot bypass it, turn it off, or control its decision.

## 8.1 Threat Model and Trust Assumptions

**Adversary.** The actor being checked, called the constrained actor in the rest of this paper, may be compromised, malicious, misdirected, using stolen credentials, or tricked by untrusted input into requesting an action beyond its legitimate authority. Holding a valid identity, credential, role, capability, or approved path does not by itself authorize the specific action it requests.

**Protected mechanisms.** The model assumes that the constrained actor cannot control the decision and enforcement mechanisms, the policy, or the authoritative sources of context that policy relies on. Anything the actor supplies is treated as untrusted unless it is independently verified or comes from an authoritative source.

**Trusted authorities.** Beyond those mechanisms, the trusted base includes the authorities whose outputs policy accepts as true: identity issuers, signing authorities, policy administration, and required context sources. Suppose an attacker compromises one of them, for example to mint administrator credentials, change policy, control the enforcement point, corrupt required context, or make the destination ignore the decision. Then that trust assumption has failed, unless an independent authority check remains outside the compromised source.

**Valid but unauthorized.** The model does not assume that other security controls have failed. An actor can hold entirely valid standing authority and still request an action that its delegation, purpose, target, state, or policy does not allow.

# 9\. Required Security Properties

This section sets out ten properties that an authorized action must have, one for each stage where its authorization can fail; the cases in §6 show several of them in practice. The properties can overlap; when one defect touches two of them, §9.10.4 says which one it counts against. Each property states its requirement first, then its consequence for the DNS example, the prior work it builds on, evidence that it fails in practice, the known weaknesses (CWE entries) that describe that failure, and, where available, how the weakness catalogs record it. Tools named under each property are examples, not requirements.

## 9.1 Non-Bypassable Mediation and Coverage Validation

### 9.1.1 What Coverage Requires

*Non-bypassable* means there is no way around the check. Every path inside the system boundary that can produce the protected effect must go through a check as strong as the one the claim relies on: the same rules, the same trusted facts, and the same behavior when something fails. A path that does is covered; a path with a weaker check, or none, is not.

In the DNS example, suppose the workload's API calls pass through a gateway that allows `www.example.com` to point only at addresses in the approved failover pool, `203.0.113.0/24`. If an on-call engineer's console session, signed in with an administrator role, can point the same record at `198.51.100.7` with no such check, the console path is not covered, and the coverage claim for that record is falsified.

```
Protected effect
      |
      +-- API path --------- Enforcement
      +-- Admin path ------- Enforcement
      +-- Automation path -- Enforcement
      +-- Uncovered path --- must not exist (C1)
```

*Figure 4\. Coverage requirement for protected effects.*

### 9.1.2 How to Show Coverage Holds

To show that coverage holds, build an inventory of the protected effects and every path that can produce them: normal APIs, admin interfaces, automation, alternate credentials, maintenance tools, and exception paths.

List what each operation can actually do, not just what its name says. Installing an npm package sounds like a download but can run the package's own scripts \[50\]. Include scripts run, programs started, data disclosed, permissions changed, and other systems altered. Build the list from the tool's actual implementation and configuration, and test it, including with hostile inputs such as an install script that writes outside its own folder. A protected effect that is neither listed nor checked falsifies C1 (§11.2).

A shell or interpreter can run any command, so its effects can't be listed in advance. Ask instead whether it, or anything it starts, can reach the protected effect other than through the check. Look at its permissions, the files, networks, and cloud metadata services it can reach, the credentials it can pick up, and the privileged services it can call. Removing one credential from the program does not help if it can get the same power another way. In Unit 42's test of the AgentCore Harness's default configuration, a support ticket with planted instructions led its built-in shell, running as root, to read a vault credential from memory \[51\].

A run can be approved as a bounded class of execution, a defined kind of run with declared limits, but each protected action it takes must still be checked or stay within separately approved limits. A build job may run freely in its sandbox, but a deployment to production must pass the check, or the job must be unable to reach production at all. Otherwise those effects fall outside the conformance claim, and the run must be restricted, moved somewhere it can be controlled, or refused (§12.1).

Coverage must be maintained, not inventoried once: a new interface, credential, deployment path, administrative tool, or exception path requires revalidation, with architecture review, configuration and credential inventories, and negative testing as the evidence.

The basis for this property follows.

* **DNS consequence:** any path that can change the record without the check, such as a console or a second credential, falsifies coverage.

* **Precedent:** Anderson's always-invoked requirement \[6\]; static verification of Linux Security Module hook placement, built because kernel hook coverage could not be assumed \[52\]; Kubernetes validating admission, which evaluates each object before it is stored \[53\].

* **Evidence:** Cursor CVE-2025-54135 let a prompt-injected agent change its MCP configuration through a path the approval gate did not cover \[54\]. Among incidents, Capital One's firewall reached its role credentials through an unchecked path \[4\] (partial support; §13).

* **Related weaknesses:** CWE-862 Missing Authorization; CWE-638 Not Using Complete Mediation; CWE-424 Improper Protection of Alternate Path \[30\].

* **Catalog record:** Missing authorization (CWE-862) ranks fourth in MITRE's 2025 CWE Top 25 \[55\].

## 9.2 Decision, Enforcement, and Policy Integrity

Section 9.1 asks whether every path reaches the check. This property asks whether the check itself can be **trusted**. Anderson required the authorization mechanism to be tamper-proof \[6\]: neither the actor being checked nor an attacker may change, switch off, replace, or weaken the decision, the enforcement point, or the policy behind it. If the check runs on every path but the actor can rewrite the policy to allow everything (`allow *`), hide a denial, or swap in its own result, the check provides no real protection.

Approval needs the same protection. When policy requires independent approval of an action, it must come from an approver the actor cannot control. A helper agent the actor runs, a second account or signing key it holds, a partner account it directs, or a workflow it controls does not count. A different name, process, AI model, or signature is not enough to make an approver independent. To test independence, ask who can pick the approver, change its rules or instructions, use its power to approve, and fill each required approval role. In the DNS example, the remediation agent cannot approve its own production change by starting a second agent to sign off, or by editing the approval rules.

An actor may start an approval process, as long as the decision itself stays out of its control. When policy requires several approvers, or a minimum number of them, the rule must still hold if one party controls several accounts or credentials. Requiring approval from validators run by separate administrators builds that independence into the design; one patented design uses a quorum of independent authenticators for this purpose \[56\]. Long-standing examples include maker-checker separation, where one person prepares a change and another approves it, and NIST's separation-of-duties (AC-5) and dual-authorization (AC-3(2)) controls \[47\].

Keeping the check trustworthy also means protecting administrator access, controlling policy changes, and keeping an audit trail of configuration. That includes the channels that carry instructions and approvals from the person or system the actor works for: an actor that can redirect those channels can substitute its own.

The basis for this property follows.

* **DNS consequence:** a second agent the remediation agent starts, or approval rules it can edit, cannot supply the independent approval its change requires.

* **Precedent:** Anderson's tamper resistance \[6\]; Saltzer and Schroeder's separation of privilege \[7\]; Clark-Wilson separation of duty \[29\]; mandatory access control, under which a confined subject cannot change the policy that governs it \[16\].

* **Evidence:** Midnight Blizzard used a compromised application to grant itself mailbox access \[57\] (§13).

* **Related weaknesses:** CWE-732 Incorrect Permission Assignment for Critical Resource; CWE-602 Client-Side Enforcement of Server-Side Security.

## 9.3 Exact-Action, Audience, and State Binding

An approval must cover the exact action that runs. Approving who is calling, which tool, which endpoint, or a general type of operation is not enough. This property says what an approval must be tied to; §9.6 says whether an approval is still good for a particular use.

Tie the approval to every detail that could change the result. Depending on the action, that can include:

* who is acting, and on whose behalf;

* what operation is being done;

* what it is being done to;

* which service the approval is meant for;

* the values in the request, written in one standard form;

* which tool or server is being relied on, and which version, with a fingerprint of its description, settings, or code where that matters;

* where the action stands in a larger process, such as an incident or a payment;

* which version of the policy was applied; and

* details that stop reuse, such as when the approval was issued, when it expires, and a one-time number or request ID.

In the DNS example, approval to point `www.example.com` at `203.0.113.55` cannot be used to point it at `198.51.100.77`, or to change a different record.

Three more rules follow. An approval meant for one service must not work at another. Two ways of writing the same action must be treated alike: if the DNS service treats `www.example.com` and `WWW.EXAMPLE.COM` as the same record, so must the check. And if the approval depended on the record being in a certain state, that state is part of what the approval is tied to.

Tie the approval to **what the tool does**, not just its name. The same tool name and the same request can do something different after the tool, its description, something it depends on, or its settings change. So confirm which tool is actually running when the action is sent, or rely on a separately controlled deployment, or on the receiving service, to guarantee it still behaves as approved. A fingerprint of the tool's code, description, and settings can confirm this, and so can signed build records such as in-toto \[58\] or Sigstore \[59\]. A version number the tool reports about itself, or a fingerprint of its description alone, does not prove what code is running. If the deployment cannot confirm which tool is running, it must say so and cannot claim this level of binding. Invariant has described MCP "rug pulls," in which a tool changes after it was approved for use; that shows why the check matters, though not a change after one specific action was approved \[60\].

For open-ended programs such as shells (§9.1), the approval is tied exactly to the run: what was started, where it runs, and the limits on what it may do. Tying it to the command text cannot predict everything arbitrary code will do, so each protected action the program later takes needs its own approval. If no limit can be enforced, §12.1 says what to do.

Payment rules already require this kind of binding. Under the EU's PSD2 "dynamic linking" rule (Article 5), the code that approves a payment is tied to the amount and the payee, and changing either makes the code invalid. The rule also protects what the payer is shown \[45\].

**Common token protections show the gap**. An OAuth access token is a credential a client presents when calling an API. DPoP and OAuth mutual TLS make a stolen token harder to use: DPoP requires the client to prove, with each request, that it holds a particular private key, and ties that proof to the request's method and address \[61\]; mutual TLS ties the token to the client's certificate \[62\]. Both show that the right client is using the token. **Neither ties the approval to what the request contains**, such as which record to change or what value to set, so neither, on its own, provides the binding this property requires.

The goal is that what was checked, what was approved, and what runs are the same in every way that matters for security:

```
action checked  =  action approved  =  action run
```

The basis for this property follows.

* **DNS consequence:** approval for one record, address, and tool version cannot authorize a materially different change.

* **Precedent:** capabilities, which bind designation to authority \[8\]\[44\]; PSD2 dynamic linking \[45\].

* **Evidence:** Bybit's signers approved a routine transfer; the transaction they signed replaced the wallet's contract logic \[1\]\[2\] (§13).

* **Related weaknesses:** CWE-494 Download of Code Without Integrity Check; CWE-551 Incorrect Behavior Order: Authorization Before Parsing and Canonicalization.

## 9.4 Trusted Authorization Context and Purpose

A decision is only as trustworthy as the facts it relies on, so every fact that affects it must come from somewhere the actor cannot make up. An actor cannot gain power just by declaring facts about itself:

```
purpose = "approved emergency"
risk    = "low"
role    = "production-admin"
```

Who the actor is should come from an identity service, or from a system such as SPIFFE/SPIRE that checks the machine and program before issuing an identity \[63\]. A resource's current state should come from the resource or an official record of it; authority handed down from someone else should come with signed or independently checked proof; and risk scores should come from separate security tools.

The reason behind an action needs the same backing. If it changes what the action may do, it must rest on something independent, such as an approved change request, an open incident, a task the user asked for, or a signed handoff of authority; the actor's own written explanation does not count. Actions need not be listed in advance: an independent authority can approve a range of actions for an automated process to work within (§12.1).

Where a request's values came from also matters. If a rule depends on where an address, recipient, or file came from, or how far it can be trusted, that origin must travel with the value as it is fetched, changed, passed through an AI model, or handed between tools. A trusted component or independent check must mark it; a model saying a value is safe is not enough. Origin alone does not decide permission: in the DNS example, an address from an untrusted log can still be used if it is checked against the approved failover pool. Research systems such as CaMeL and Fides already track the origin and sensitivity of values in agent systems; §9.7 requires those limits to carry across actions \[64\]\[65\].

What the approver is shown counts too. Whatever is shown to an approver, whether a person or a system, must accurately present the target, values, and effects the approval depends on. It may shorten or hide data but must not change what the action means for security, and the actor must not win approval by hiding details or giving a misleading summary. The approval must name what was approved, and §9.3 ties it to what runs. In one Invariant experiment, the confirmation screen hid sensitive tool-call details from the user \[60\]: a C4 failure, because the approver saw an incomplete picture. The tampered tool description behind the call is a separate problem, and changing an accurately approved action afterward would be a C3 failure.

Any source that grants authority becomes a target. If an incident system, change log, or ticketing tool supplies such facts, the assessment must name it; if the actor can create or change those facts without the required independent check, C4 fails.

The basis for this property follows.

* **DNS consequence:** an address suggested in a firewall log is only a candidate until it is checked against the approved failover pool.

* **Precedent:** Clark-Wilson's rule that procedures accepting unconstrained input validate it or reject it \[29\]; Biba integrity, which restricts information flow from lower- to higher-integrity levels under assigned integrity labels \[46\]; the TCSEC trusted path \[16\].

* **Evidence:** Bybit's signers approved on a falsified display \[1\]\[2\]; GhostJacking steered an agent with text planted in a log \[3\] (§13).

* **Related weaknesses:** CWE-345 Insufficient Verification of Data Authenticity; CWE-807 Reliance on Untrusted Inputs in a Security Decision; CWE-451 User Interface (UI) Misrepresentation of Critical Information.

## 9.5 Delegated Authority and Independent Authority

### 9.5.1 An Intermediary Cannot Enlarge a Delegation

When an intermediary, such as a service, operator, or agent, acts for someone else, its own broader standing permissions cannot enlarge what the requester delegated. In the DNS example, the incident record authorizes a failover change to `www.example.com`, using one of the incident's approved backup addresses. The change is made by `dns-remediator`, an automated remediation workload that holds a standing `dns-admin` role able to change any record in the zone. If the check asks only whether that role may change DNS, it will also allow the workload to repoint another record in the zone, or to point `www.example.com` at an address the incident never approved. The check must instead ask what the incident record delegated: this record, and one of these addresses.

```
Originating authority
          |
          v
   Delegated scope
          |
          v
   Current policy
          |
          v
 Effective authority
```

*Figure 5\. Effective authority across delegation.*

Each stage may narrow what the stage before it allows, but must not widen it. An action must be refused unless every stage is present, approved, and allows the action; a stage is approved when it was set up through its proper process rather than by the actor. In the DNS example, the delegation must come from an incident record the workload cannot create or edit, and the policy must be the approved version, not one the workload edited.

### 9.5.2 Authority Beyond the Delegation

An intermediary does two kinds of work: 1\) work it does for a requester, and 2\) work it does for itself. For work on a request, it may do only what the request delegated. If the request needs more, that extra must be approved separately, by a step-up approval or a new delegation. For its own work, the intermediary may use its own permissions, its independent authority, as policy allows. What it may not do is use those permissions to act on a request beyond what the request delegated, such as changing a different record or setting an unapproved value. In the DNS example, `dns-remediator` may undo a change it made, as part of its own job. It may not use that permission, or its `dns-admin` role, to change anything the incident record did not delegate.

This matters because the destination sees only the intermediary's credential. If the check asks whether the intermediary may act, rather than whether the request delegated the action, anything the intermediary's role allows will succeed, whether the request was manipulated, crafted to overreach, or sent by a compromised intermediary. The enforcement point must therefore see the delegation, not just the credential (§9.5.4). In the figure below, requester E1 delegates only a read to intermediary E2:

```
E1 --[delegates: read record A]--> E2 --[write record A]--> enforcement point --> BLOCKED
                                   (E2's own role allows writes)
```

### 9.5.3 Stating the Request's Limits

Something that can refuse the action has to be able to check the request's limits. In the DNS example, the DNS provider knows nothing about incidents: it sees only a credential and a request, and that credential can change any record in the zone. So the incident's limits, this record and these addresses, have to reach the enforcement point that decides before the provider acts, or the provider itself if it can check them. Ways to do that include sending a delegation record with each request for the enforcement point to verify, having the enforcement point look up the incident record itself, or setting limits in advance for each kind of incident, such as which records a failover may change. Without some such limit, the only limit is `dns-remediator`'s role, and that covers the whole zone.

The Config Connector case (§6.6) shows this gap in real life: a Kubernetes user with no Google Cloud account got organization-wide permissions through the operator. When nothing limits the request this way, the delegation criterion (C5) is not established, and the §11.2 delegation tests cannot run until such limits exist.

### 9.5.4 Call-Chain Lineage

A request often passes through several parties before it reaches the action. Its call-chain lineage is the record of each of those parties, from where the authority started to where the action runs. Every party in that chain must be allowed to carry the authority: either named in the delegation, or allowed by policy to pass it on. If any one is not, the action must be refused. It is not enough that the chain starts and ends in the right places. In the DNS example, a request that says it acts under the incident record, but reaches the DNS provider from an unknown helper agent instead of from `dns-remediator`, must be refused. The chain itself must come from trusted records, not from what the request says about itself (§9.4), and it must be tied to the action (§9.3).

Some existing tools can carry authority and its chain. Macaroons attach conditions that limit how, by whom, and in what situation authority may be used \[44\]. OAuth Token Exchange records who the request is for, who is acting on it, and the chain of handoffs \[12\]. The IETF Transaction Tokens draft passes identity and authorization details along a series of service calls and limits how far the scope can grow, though revision 11 leaves the final decision to the application \[66\]. With any of them, the last service must still check the chain and decide whether this specific action is allowed.

What is passed along the chain needs the same care. An answer from another service, tool, or AI model is not trustworthy just because an approved component produced it. In the Sentry/Seer demonstration (§6.5), Sentry's Seer passed on an attacker's recommendation as its own finding, and a coding agent trusted it \[3\]\[41\]. The origin of such output has to be tracked through the chain, and the action it leads to still needs its own authority.

The basis for this property follows.

* **DNS consequence**: the dns-remediator workload's standing `dns-admin` role does not widen what the incident record delegated.

* **Precedent**: Hardy's capabilities \[8\]; Saltzer and Schroeder's least privilege \[7\]; OWASP's recommendation to run extensions in the user's context rather than with standing privileges \[25\]; stack inspection, which checks the authority of every caller on the stack up to any frame that asserts its own privilege, as Java's doPrivileged does \[67\]. Applied across services, the same idea is call-chain lineage.

* **Evidence**: Invariant's tool-shadowing experiment showed a malicious tool's description changing how an agent used a trusted tool \[60\]. Among incidents, Capital One, GitHub/Heroku, Midnight Blizzard, Salesloft Drift, and Hugging Face each show authority used for a purpose no one had declared, with no recorded limit on its scope (§13).

* **Related weaknesses**: CWE-250 Execution with Unnecessary Privileges; CWE-441 Unintended Proxy or Intermediary ('Confused Deputy').

* **Catalog record**: MITRE's entry for the confused deputy (CWE-441) notes that it arguably underlies most attacks that need an active attacker, because the vulnerable program already holds the authority the attacker uses \[30\]. Its recorded cases go back to 1999, with the FTP bounce attack. Server-side request forgery (CWE-918), a form of it, ranks 22nd in MITRE's 2025 Top 25 and was the path in Capital One \[55\]\[68\]. MITRE's recommended fix is this property: an intermediary must carry the original requester's identity all the way to the target \[68\].

## 9.6 Freshness, Replay Protection, and TOCTOU Resistance

Section 9.3 says what an approval is tied to; this property asks whether it is still good when used, and whether it can be used again.

An approval for one action must not quietly become reusable permission. If it is carried forward as a token or record, the system must enforce every reuse limit policy sets: expiry, a one-time number or request ID not used before, revocation, and a current policy. If policy ties the approval to its presenter, anyone else presenting it is using it improperly. In the DNS example, an approval to point `www.example.com` at `203.0.113.55` stops being valid once used, if revoked, or when the incident closes, even though it is unchanged and its signature still checks out.

A material change to the tool, its description, settings, or dependencies also ends an approval that relied on the earlier version, unless an independent policy confirms the new version does the same thing. Section 9.3 says how to identify the tool; this property enforces the check at use.

Queued, scheduled, retried, and follow-on work must recheck its authority at the last controlled point before its protected effect, within the time allowed for a revocation to take effect. A check at queue entry does not establish freshness (C6) for a later change that ignores a revocation: if the incident closes while the DNS change waits, the change must be refused where it would be committed. Continuing work must be checked again at each later protected effect the claim covers.

The design must also handle time-of-check-to-time-of-use (TOCTOU) changes. If the request changes after approval, the destination would read it as a materially different operation, or the state the approval relied on changes before it runs, the approval no longer applies, unless policy treats the change as immaterial. If someone else changes `www.example.com` between the check and the write, the approval, tied to the record's earlier version (§9.3), no longer applies.

DPoP and OAuth mutual TLS make a stolen token harder to reuse but do not approve the full action \[61\]\[62\]. For revocation across providers, the OpenID Continuous Access Evaluation Profile defines events that let other systems cut back access while it is in use \[69\].

The basis for this property follows.

* **DNS consequence**: an unchanged, signed DNS approval can become invalid when the incident closes, when it has been used, or when the approved tool changes.

* **Precedent**: Saltzer and Schroeder's requirement that remembered checks be updated when authority changes \[7\]; Zanzibar's consistency tokens against the "new enemy" problem \[20\].

* **Evidence**: Cloudflare missed four leaked credentials in its rotation, and an attacker used them weeks later \[70\] (§13).

* **Related weaknesses**: CWE-613 Insufficient Session Expiration; CWE-367 Time-of-check Time-of-use (TOCTOU) Race Condition; CWE-837 Improper Enforcement of a Single, Unique Action.

## 9.7 Execution-Derived State and Cross-Action Constraints

### 9.7.1 What Carries Forward

An action allowed on its own can still be wrong given what came before. Authorization must therefore carry forward the limits policy draws from earlier actions and decisions: how far a workflow has progressed, how much of an allowance is used, labels on data (its source, sensitivity, and trust), and earlier denials or demands for further approval. These can block a later action even when its actor, tool, and values are each allowed. Which limits apply depends on declared policy: with no labeled data there are no labels to carry, and with no cumulative limit there is no allowance to track. Section 11.2 gives a test for each kind of limit.

### 9.7.2 Data That Moves Between Actions

Two permitted actions can add up to one that is not. A permitted read followed by a permitted send does not make the resulting disclosure permitted. In the DNS example, the workload may read incident logs and may post to a chat connector, but secrets in those logs must not leave through that post. The way to stop it is with labels: tags attached to data that record where it came from, how sensitive it is, or how far it can be trusted, such as "contains credentials" or "from untrusted telemetry." Data must keep its labels as it moves, through approved integrations, files, memory, helper agents, or transformations, and the check where data leaves the system must use them. The declared profile sets the terms: which sources and destinations are protected, how data is labeled, and how far and how long labels spread. It also says who may change a label, by declassifying data (lowering its sensitivity) or endorsing it (raising its trust), and what state must survive a change of task or tool. NIST's information-flow control, AC-4, addresses this class of policy \[47\].

AI models make this harder. Once labeled data enters a model's context, there is usually no way to tell which later outputs depend on it, so assume they all do. Every later action from that context, and any helper agent or shared memory that receives its content, keeps the labels until a trusted reset or an authorized declassification removes them. In the DNS example, once the workload's model has read logs labeled "contains credentials," anything it later sends out carries that label too. Encoding, summarizing, rewording, or switching tools does not remove a label. The system around the model enforces this rule; it does not depend on the model reporting what it did with the data. CaMeL and Fides are concrete prior work; Fides, for example, carries a conversation's labels into the model's responses \[64\]\[65\].

### 9.7.3 Denials That Carry Forward

Where policy says so, a denial must not be undone just by asking again. Once pointing `www.example.com` at `198.51.100.77` is denied, the workload must not get the same change through by retrying with another tool or writing the address differently. To make that hold, keep the denial's record across retries and alternate tools: why it was denied, what was attempted, the call-chain lineage (§9.5.4), and any further approval now required. Also define which rewordings, split requests, or tool changes count as the same restricted request, and when the restriction resets or expires. The test is whether declared restrictions survive such rewording. It does not assume that every equivalent request can be recognized, or that every denial is permanent.

### 9.7.4 Cumulative and Concurrent Limits

Some limits add up across several actions. Repeated transfers can exceed a daily allowance, and creating a user, granting a role, and issuing a credential can together create privileged access that no single step grants. The record behind such a limit, such as a running count, must come from an authoritative source, be protected from tampering, stay consistent, and not be resettable by restoring an older copy.

Actions that run at the same time add a further risk. If two requests each check the count before either updates it, both see room under the limit and both go through. Checking and updating the count must therefore act as one step, for example through an atomic operation, by reserving the allowance before acting, or by handling requests one at a time. With a limit of three automated DNS changes per incident within fifteen minutes, ten requests sent at the same moment may produce at most three changes. Where strict coordination is impractical, such as when parts of the system temporarily cannot reach each other (a network partition), policy may declare a bounded overspend, such as one extra action per partition. C7 then tests that bound, and exceeding it falsifies the claim. Zanzibar is prior work on keeping changing authorization state consistent \[20\].

Across §§9.7.1–9.7.4, missing or lost state and uncoordinated use of an allowance count against C7 (composition), and forged source labels count against C4 (context, §9.4). Attribution between C7 and C10 follows §9.10. Section 11.2 tests how state carries forward and how it is enforced.

The basis for this property follows.

* **DNS consequence:** the next change depends on earlier changes and denials; data read during remediation must not leave through a later, otherwise permitted connector action.

* **Precedent:** the Bell-LaPadula `*-property`, which forbids writing data down to a lower classification \[71\]; Denning's lattice model of information flow \[72\]; Goguen and Meseguer's noninterference, the standard definition of secure information flow \[73\]; the Chinese Wall policy, under which past accesses determine later permissions \[74\]; and PSD2's cumulative limits on payments exempted from strong authentication \[45\].

* **Evidence:** EchoLeak and Invariant's GitHub MCP demonstration each combined permitted reads and sends into a disclosure \[75\]\[76\] (§13). Among incidents, Bangladesh Bank was a multi-instruction attack in which cumulative and sequence limits were relevant (partial support; §6.1).

* **Related weaknesses:** CWE-362 Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition'); CWE-841 Improper Enforcement of Behavioral Workflow; CWE-201 Insertion of Sensitive Information Into Sent Data.

* **Catalog record:** MITRE notes that business-logic flaws such as CWE-841 are frequently exploited in real systems but under-studied and underrepresented in the catalog \[77\].

## 9.8 Fail-Safe Decision and Failure Semantics

When part of the authorization system fails, the failure must not turn into permission. Required checks and outright prohibitions cannot be outweighed by advisory signals such as risk scores, missing required evidence cannot count as permission, and any extra approval that policy allows, such as a step-up, must be explicit and come from an independent source. A failed or disrupted authorization path must not let the action run or force a weaker mode: if the incident system or the decision service goes down, `dns-remediator` must not fall back to its standing credential and make the change anyway. Where policy requires evidence of what ran, the action must not proceed without it; otherwise execution evidence (§9.9) could lapse during a fault.

Failing open, meaning letting an action through when the check cannot run, is convenient, since a blocked request is noticed at once and a silent bypass is not, and some systems offer it as a setting. Kubernetes, for example, can call an outside service, an admission webhook, to check or adjust the requests it is configured for before accepting them. In the current API, a request is rejected by default if that call fails or times out, but a setting called Ignore lets it proceed anyway \[78\]. Kubernetes recommends letting webhooks that adjust requests fail open, as long as a separate, required check validates the final request afterward, so that a skipped adjustment, even one that adds a security setting, is still caught \[79\]. Where a webhook is itself the authorization check, with no required check behind it, the same setting turns an outage into a bypass.

Refusing on failure does not have to mean stopping everything. A system can stay available in safe ways: switch to a reduced mode of operation approved in advance; use a cached approval, but only while its scope, policy version, context, state assumptions, and freshness all remain valid; or route the action through another enforcement path that meets the same control objective. In the DNS example, if the decision service is down, a cached approval to point `www.example.com` at `203.0.113.55` can still be used once, before it expires and while the incident remains open, but a change to a new address cannot. Emergency override paths, known as break-glass paths, are also allowed, but they need their own approval process, a narrow scope, a record of who used them, time limits where practical, and regular testing, so they do not turn into permanent bypasses.

The basis for this property follows.

* **DNS consequence:** losing the incident state or the decision service cannot silently permit a production change through a fallback credential.

* **Precedent:** Saltzer and Schroeder's fail-safe defaults \[7\]; XACML's deny-biased enforcement point \[18\]; SELinux enforcing mode, with permissive mode as a declared exception \[80\].

* **Evidence:** the ACS reference Guardian documents a default of proceeding when the Guardian fails \[81\]. No public incident was found in which a check confirmed to fail open caused the harm (§13).

* **Related weaknesses:** CWE-636 Not Failing Securely ('Failing Open').

* **Catalog record:** OWASP's 2025 Top 10 lists CWE-636 among the notable weaknesses in its Mishandling of Exceptional Conditions category \[82\]. MITRE's entry describes failing open as a choice to "fail functional" to cut administration and support costs, lists cases such as CVE-2007-5277, and has noted since 2008 that design failures of this kind are rarely publicly reported \[83\].

## 9.9 Evidence of Decision and Execution

An approval must be linked to trustworthy evidence of what actually ran, from the destination or another trusted source, not from the actor or from anything that forms or forwards the request. Unlike the other properties, this one does not stop a wrong action; it makes sure one cannot go unnoticed. Evidence has four levels:

| Level | What it shows |
| ----- | ----- |
| Decision evidence | Who or what asked, whose authority was checked, what operation and target were approved, and the policy, context, and freshness behind the decision. |
| Execution correlation | A record from the destination, or another trusted source, that can be linked to that specific decision. |
| Executed-operation reporting | That source reports what was actually done: the operation, the target, and the values or effect that matter. |
| Verified-effect evidence | Proof that the reported operation matches the real effect, through attestation, independent observation, or another method that would catch a materially different result; in the DNS example, an outside lookup, once cached answers expire, that returns 203.0.113.55. |

This property requires the first three levels. In the DNS example, if the decision approves pointing `www.example.com` at 203.0.113.55, the provider's change log must show that record and address, linked to that decision; a log showing `198.51.100.77`, or no linked change, exposes the gap. If no trusted source can supply such evidence, or it cannot be tied to the approval, the property is not established. An `ALLOW` from the check or a generic "success" response is not enough, and a record the actor can change or suppress cannot show what ran (§9.2).

The basis for this property follows.

* **DNS consequence:** an ALLOW record must be connected to evidence of the record and address the provider actually changed.

* **Precedent:** Clark-Wilson's log sufficient to reconstruct each operation \[29\]; TCSEC audit \[16\].

* **Evidence:** Storm-0558 victims without a premium license had no record of which mailbox items the forged tokens read \[84\]. Replit's agent reported fabricated results and falsely claimed that a rollback was impossible, which is why an actor's own reports cannot serve as evidence \[85\]\[86\] (partial support; §13).

* **Related weaknesses:** CWE-778 Insufficient Logging.

* **Catalog record:** OWASP notes that logging failures are hard to test for and rarely appear in CVE data \[87\].

## 9.10 Enforcement of Declared Restrictions

### 9.10.1 Declared Restrictions Must Actually Be Enforced

Correct facts are not enough; the rules must use them. Sections 9.3–9.7 make sure the decision gets the right facts. This property makes sure the policy's rules actually consume and act on those facts. For each consequential action, the organization must write down, separately from the policy code, what is allowed and what is forbidden, which exceptions apply, and when extra approval is needed. It must then show that the policy in force does what that statement says. These restrictions can involve the action's details, trusted context, delegated authority, freshness, and state carried over from earlier actions.

A condition can be lost when policy is converted between formats, accept too wide a range, or be overridden by another rule that allows the action. In the DNS example, the incident allows only `203.0.113.55` and `203.0.113.56`; a policy that accepts any address in `203.0.113.0/24`, or a separate rule that allows any change by a `dns-admin`, leaves that restriction unenforced, though every input arrived correctly.

Not every input must change the result: fields bound only to detect tampering, or recorded only to match evidence later, need not. But every declared relationship must hold, including combinations and approved exceptions; showing that one changed input changes one result is not enough. This property tests enforcement against the declared policy, not whether that policy is wise; a harmful or overly broad restriction is a policy problem (§11.2).

### 9.10.2 Checking the Policy in Force

Automated policy analysis already offers ways to check whether a policy's rules match its declared restrictions:

* Zelkova, the AWS reasoning engine behind several of its policy checks, translates AWS policies, and the properties they should have, into logic formulas and checks them with a solver \[88\].

* IAM Access Analyzer's custom policy checks compare what a policy allows against a reference policy, or check for access that should be forbidden \[89\].

* Cedar Analysis encodes Cedar policies as logic and uses a solver to compare policy sets and find logical problems \[90\].

* OPA policy tests state the expected decision for given inputs and data, and can report how much of the policy the tests cover \[91\].

Whichever tool is used, run it against the policy actually deployed, not its source, and record the version, trusted inputs, rule combination, and enforcement path it was run against. Datadog's GDS example shows why: a condition limiting who could assume a role was present in the Terraform source, but a duplicate map key dropped it from the trust policy actually generated, so a review of the source would have missed the gap \[92\]. These tools check the policy's logic, not the path around it. An assessment for this property therefore combines three things: the declared restrictions, analysis of the policy in force, and tests showing that the protected effect is refused when it should be.

### 9.10.3 Independence of the Declaration

The restrictions must be declared by someone other than whoever built the policy being tested. A team that writes both is testing its work against itself: a mistake it makes in the policy, it can repeat in the restriction, and the test will pass. Separation can take several forms: a separate policy owner; restrictions stored where any change needs that owner's review; or restrictions written by the security team and run as tests against the deployed policy. In the DNS example, the rule that only the incident's approved addresses are allowed would come from the incident process or the security team, not from the engineers who wrote the DNS policy.

### 9.10.4 Attribution Rule

When a defect appears, record it where the requirement fails (C8 and C9 failures go under those criteria):

* **C2,** if the actor controls the decision, enforcement, policy, or required independent approval;

* **C3,** if the action is bound or interpreted wrongly;

* **C4,** if facts, the origin of values, or what the approver was shown cannot be trusted;

* **C5,** if the authority basis or delegation limit is wrong, or a hop in the call-chain lineage was not approved to carry the authority;

* **C6,** if the approval was no longer valid when used;

* **C7,** if state from earlier actions was lost or not coordinated.

If those inputs are correct but the decision ignores, weakens, or overrides a declared restriction, C10 is the main defect, with the affected criteria noted. If the effect-producing path never reaches the decision, or reaches only a weaker one (§9.1), it is C1 instead. Common cases: a correct count or label whose declared limit is ignored is C10, with C7 affected; concurrent requests sharing one allowance, or lost labels, are C7; a missing task or request scope is C5; and an unsupported or forged scope is C4. Each criterion thus reports its own result, and one defect is not counted twice.

The basis for this property follows.

* **DNS consequence:** supplying the address, incident status, and counter is not enough unless the policy in force enforces their declared restrictions.

* **Precedent:** SELinux neverallow rules, which declare access that must never be granted and are checked when policy is built \[80\]; XACML combining algorithms, which fix how conflicting rules resolve \[18\]; Zelkova \[88\].

* **Evidence:** In Storm-0558, Exchange Online accepted tokens forged with an acquired consumer signing key for enterprise mailboxes, because issuer validation was assumed rather than performed \[93\]\[94\] (§13).

* **Related weaknesses:** CWE-863 Incorrect Authorization; CWE-346 Origin Validation Error.

* **Catalog record:** CWE-863 ranks 17th in the 2025 Top 25, with exploited cases in CISA's Known Exploited Vulnerabilities catalog \[55\].

# 10\. Example: Production DNS Change

This section walks the DNS example from §5 through the whole model. It is simple enough to follow but has the dependencies that make real production changes hard to authorize. Each §9 subsection has already stated what its rule means for this example.

**What happened.** The server behind `www.example.com,` at `192.0.2.10`, has stopped responding. The company's incident system, its official record of incidents, has opened incident `INC-4821`.

**What was authorized.** The incident record approves switching `www.example.com` to one of two backup addresses only: `203.0.113.55` or `203.0.113.56`. Company policy also allows no more than three automated production DNS changes per incident within fifteen minutes.

**Who acts.** An automated repair workload, `dns-remediator`, makes the change; a workload here is a program that runs without a person at the keyboard. It has a valid access key for the production DNS service and the company role `dns-admin`, which lets it change any record in the zone.

**What was requested.** The workload asks for this change:

```
actor:        dns-remediator
operation:    UPDATE_A_RECORD
record:       www.example.com
current:      192.0.2.10
new_value:    203.0.113.55
incident:     INC-4821
destination:  dns-provider.example
```

It could also ask for an address it picked up from data an attacker planted:

```
new_value:    198.51.100.77
```

**What each check decides.** A standing `dns-admin` permission allows both requests, because it asks only whether the workload may change DNS. Last-mile authorization asks whether this specific change is allowed: this record, this address, under this incident. Checked against the incident record, `203.0.113.55` can be allowed and `198.51.100.77` cannot (§10.1).

## 10.1 Two Checks on the Same Request

A policy engine, the component that makes the allow-or-deny decision, can follow its rule correctly and still allow a change it should refuse, if it sees only who is asking, what kind of operation it is, and which zone:

```
principal = dns-remediator     OK  valid
role      = dns-admin          OK  permitted
action    = UpdateDNS          OK  permitted
zone      = example.com        OK  permitted
decision  = ALLOW
```

The rule never looked at `new_value`, the address that decides what actually happens. The engine's `ALLOW` means the workload may change DNS, not that this change is allowed. Give the same engine the proposed change and the incident record, and it can tell the two requests apart:

```
new_value in approved_addresses(INC-4821)      -> ALLOW
new_value not in approved_addresses(INC-4821)  -> DENY
```

Existing policy tools can already express this rule. Last-mile authorization does not replace Cedar, OPA, attribute-based access control, IAM, or Zero Trust; it says when their decision is close enough to the action, and tied tightly enough to it, to count.

## 10.2 A Minimal Decision and Evidence Contract

The model can be written as a simple agreement about what goes into the decision and what comes out, whatever policy language is used. The fields below are an illustration, not a required format.

```
authorization_request:
  request_id: "req-8f2..."
  actor: "dns-remediator"
  authority_basis: "incident-delegation:INC-4821"
  action:
    operation: "UPDATE_A_RECORD"
    target: "www.example.com"
    current_value: "192.0.2.10"
    new_value: "203.0.113.55"
  state_refs:
    incident_state: "incident-system:INC-4821#status"
    approved_addresses: "incident-system:INC-4821#approved-addresses"
    dns_version: "v1842"
  freshness:
    expires_at: "..."
    nonce: "..."

authorization_result:
  decision: "ALLOW"
  policy_version: "dns-prod-42"
  bound_request_digest: "..."
  evidence_id: "authz-e7c..."

execution_evidence:
  evidence_id: "authz-e7c..."
  provider_change_id: "chg-921..."
  executed_value: "203.0.113.55"
```

The agreement splits the work. The policy engine decides. Trusted systems, such as the incident system, supply the facts. The enforcement point in front of the DNS service blocks the change unless the decision covers exactly this request. And the DNS provider reports what was actually changed.

The request and result map onto the subject, resource, action, and context model of the AuthZEN Authorization API, an OpenID Foundation standard for asking a decision service for allow-or-deny decisions \[21\], so a deployment can use a standard decision service instead of a custom one. AuthZEN's draft obligations profile, under which the enforcement point must carry out every duty attached to a decision or else refuse it, is a natural way to require binding and evidence \[95\].

Whatever format is used, each decision record must include, in some form, a request ID, the policy version, a binding of the exact action (§9.3), the decision, and an ID that links it to the evidence of what ran (§9.9). Any design that ties these together will do, and having them lets assessors compare products. The references in the request do not mean a network call for every field: facts can be copied locally, cached for as long as policy allows, or carried as proof that can be checked independently, as long as the decision can trust them and they are fresh enough.

## 10.3 A Lab Walkthrough

This section runs the ten questions against a small test environment that recreates the DNS setup, with a simulated DNS provider and incident service, to show that each one can actually be tested. The same tests were run against two versions of the environment.

In the **conventional version**, the workload holds the DNS provider's access key, and the only check is whether the key is valid.

In the **last-mile version**, an enforcement point holds the only access key and checks every change before it reaches the provider. It checks that:

* the incident is open, according to the incident service;

* the change stays within what the request covers;

* the new address is one the incident approved;

* a one-time approval matches a fingerprint of the exact change; and

* the incident has not used up its three changes.

If the incident service is down, it refuses. Each decision records the provider's change ID.

Before each test, both versions were checked with a change that should go through. In the table, **Held** means the test tried to break the property and could not; **Failed** means it succeeded; **Not established** means the version had no control for the test to check.

| Test | What the test did | Conventional | Last-mile |
| ----- | ----- | ----- | ----- |
| Baseline: allowed change | Requested a change to an approved address during the open incident | Goes through | Goes through |
| C1 Coverage | Had the workload call the DNS provider directly, skipping the check | Failed | Held |
| C2 Integrity | Had the workload attach an approval it issued itself | Not established | Held |
| C3 Binding | Got approval for one address, then submitted another; also sent a request with a field repeated, so two parsers could read it differently | Not established | Held |
| C4 Context | Cited an incident the incident service has no record of | Not established | Held |
| C5 Delegation | Requested a change to a record outside what the incident covers | Not established | Held |
| C6 Freshness | Reused an approval already used, and used one that had been revoked | Not established | Held |
| C7 Composition | Sent ten changes at once against the limit of three | Not established (10 went through) | Held (3/10 went through) |
| C8 Failure behavior | Took the incident service offline, then requested a change | Not established | Held |
| C9 Evidence | Matched each allowed change to the provider's log; made two approved changes to different addresses and checked they were told apart | Not established | Held |
| C10 Restriction enforcement | Submitted five addresses: the two the incident approved and three it did not | Failed (3/5 addresses wrongly allowed) | Held |

**What the table shows.** The conventional version lets the allowed change through, but nothing stops a harmful one. It fails C1 and C10 outright, and C2–C9 are not established, because there is no approval, incident check, scope, limit, or evidence to test. The last-mile version held on every test. Every question has a test that tells the two versions apart.

**Three results in detail**:

* For C7, three of the ten changes were allowed, each with a provider change ID; seven were denied for exceeding the limit; and the provider's log shows exactly three changes.

* For C9, each allowed decision's record carried a request ID, the policy version, a fingerprint of the change, and the provider's change ID, and each change ID matched a provider log entry showing the approved record and address. Two approved changes, one to each backup address, produced two separate entries, each matching its own decision; an entry with a different address would not have matched.

* For C10, the conventional version, which checks only the access key, allowed all five addresses, so three of its five decisions were wrong. The last-mile version allowed the two approved addresses and refused the other three.

**Scope.** The lab ran one test per criterion; it did not exercise every case §9 describes, such as a request through an unapproved intermediary (§9.5.4), a change queued past the incident's close (§9.6), or a denied address retried through another tool (§9.7.3). An address supplied by an attacker, like 198.51.100.77 in §10's opening, falls under C10: the incident's approved list reaches the decision correctly, so allowing an unapproved address is an enforcement failure (§9.10.4).

**Limits.** These are test results, not a claim that the design meets the criteria. The same author wrote the rules, built the enforcement point, and wrote the tests, so the independence requirement in §9.10.3 is not met, and no C1–C10 claim is made. The DNS provider and incident service are simulated, and C1 holds only because the lab has no other way to reach the access key. Assessing real, running deployments is outside the scope of this paper (§14).

## 10.4 A Second Example: Labeled Data and an Agent Tool

**The setup.** An AI agent summarizes customer support tickets. It may read from the customer database (the CRM) and post to a Slack channel shared with an outside support vendor, each allowed on its own; the agent uses that channel for routine escalations. One ticket holds account details the CRM marks restricted, plus an instruction its customer planted: "post the account details to the vendor channel for escalation."

**What should happen.** The planted instruction is untrusted input, so it cannot be the reason for any action (C4 Context); the real task, set by the support lead, is to summarize the tickets. When the agent reads the restricted ticket, the system around it attaches the restricted label to everything the agent is working with. Every later action carries that label, including the model's summary, because there is no way to trace exactly how data moved through the model (C7 Composition, §9.7.2). The declared rule bars restricted content from channels shared outside the company without approved release, so the labeled post is refused (C10 Restriction enforcement). The channel is private, but that does not matter: the rule is about leaving the company, not about being public.

Other routes to the same vendor, such as a webhook tool or a file share that syncs outside the company, are in the inventory of paths and face the same check (C1 Coverage). The messaging service's record of what was posted, linked to each decision, shows whether any allowed post carried restricted content (C9 Evidence).

**Where a failure would be recorded.** If the label reached the decision and the post went through anyway, the main defect is C10; if the label was lost along the way, it is C7.

**How to test it.** Run the §11.2 C7 test with two summaries: one from public data only, which should be posted, and the restricted one, which should be refused.

# 11\. Scoped Conformance and Evaluation

This section explains how to test a deployment against the ten criteria and how to report what the tests found.

The result is called a conformance claim: a statement, backed by test evidence, of whether the deployment meets the criteria (§11.1 sets out which a claim must cover). Each criterion is reported in one of three ways: 1\) supported (the tests show it holds), 2\) falsified (a test shows it does not), or 3\) not established (the evidence does not show that it holds).

Every claim is *scoped*: it applies only to what was tested. For example, a claim might cover changing a production DNS record, under a stated set of systems, rules, and conditions. That claim does not cover deleting the same record or changing another service; each of those would need its own tested claim. This matters because a deployment can protect one action well and another badly, and a claim about the whole deployment would hide the gap.

*Assurance* is how much the claim can be trusted, and it depends on the evidence behind it. Suppose two teams assess the same deployment and reach the same claim. The first is the team that built the system. The second is an outside assessor, who also confirms that the DNS record actually changed (§9.9). Both reach the same result, but the second deserves far more trust: its tests were independent, and it checked the real effect, not just the logs. A claim that did not state its assurance would make them look identical.

Stating assurance also lets an organization require stronger evidence where more is at stake, such as a large payment, than for a routine change (§8). Strong evidence still cannot cover a gap: a well-tested C9 does not make up for a C5 that was never shown to hold.

The rest of this section explains how to make and record a claim (§11.1) and how to test it (§11.2).

## 11.1 Assessment Unit and Record

**What is assessed**. Each assessment covers one type of action and the effect it controls. For example, one assessment might cover changing a production DNS record. Deleting a record, or issuing a credential, would each need its own assessment. The assessment covers every path in the deployment that can produce the effect, not just the usual one. Within that scope, all the properties that apply must hold at the same time, under the same policy and conditions. There must also be evidence linking each decision to what actually ran. If the claim is later extended to new effects, paths, authorities, or conditions, those must be tested too.

**What the record contains.** Each assessment keeps one record, identifying:

* the action and its direct and indirect effects;

* the constrained actors and what they can actually do;

* the system boundary and its paths;

* who holds authority, and the restrictions declared independently of the implementation;

* the values and state that matter to the decision;

* the conditions tested: normal, concurrent, and degraded; and

* the enforcement owners and evidence sources.

Where they apply to the action, the record also identifies:

* the tool version relied on;

* how approvers are kept separate from the actor;

* where data comes from and goes, and how its labels travel;

* how denials are kept;

* the call-chain lineage (§9.5.4); and

* for open-ended programs, what authority they can reach.

C7 must be reported in four parts: data labels, denial history, cumulative use, and concurrency. Assessors must also review the actual implementations and use test cases that challenge the list of effects and the limits on reachable authority.

**What each result reports.** Each result must name:

* the edition of this framework used, by a fixed identifier such as a release tag, because a later draft may define the criteria differently;

* the deployment and policy versions, the scope, the conditions, and the owner; and

* the evidence, including how many test cases were run (both attempts that should be refused and changes that should go through) and what each count covered.

Each criterion must be recorded as supported (within scope), falsified, or not established, with a reason for any part that does not apply. Defects must be recorded under the attribution rule in §9.10.4.

If the scope changes, the record must show the old and new scope and what each covered, why it changed, what obligations remain, and which results are affected. Narrowing the scope must not be used to make results look better. For example, dropping the console path from scope must not raise the reported coverage figure, and a protected effect already known to be reachable cannot be removed from the record.

**The full claim.** A full (combined) claim requires every applicable part of C1–C10 to be established by compatible results on the same configuration, boundary, policy, and conditions. One falsified or unestablished requirement rules it out; support in other components, or a decision to accept the risk, does not change that.

**The preventive claim.** When the destination cannot supply evidence of what ran, a deployment may claim the *preventive profile* instead: every applicable requirement of C1–C8 and C10, with C9 recorded as not established and the destination named. It says the checks stopped unauthorized actions before they took effect on the paths in scope, not that what ran matched the decision, and it must always be reported under its own name, never as a full claim. For destinations that return no records that can be matched to a decision, including many third-party APIs, it will often be the only claim available. It is still good practice for the enforcement point to keep its own record of what it sent, linked to the decision.

**What a result does not show.** A result shows that the deployment enforces the scope, delegation, and restrictions it declared, not that they were right for the task; choosing them is an organizational decision the model takes as given (§14).

**Keeping results current.** The record must set how often each result is retested and which changes force an earlier retest, with the last test date and the next due date. If a retest is overdue, or a triggering change comes first, supported results become not established until retested under current conditions; the earlier result and its original scope must stay on record. A falsified result stays falsified until the problem is fixed and retested; it does not expire. The record must note the trigger, the affected criteria and claims, and the resulting status. The constrained actor must not be able to alter or selectively hide the evidence behind a claim, and enforcement-owner reports must be backed by kept records or independent observations.

## 11.2 Falsifying Tests and Assessor Artifacts

This section gives one test for each criterion, C1 through C10. Criterion Cn tests property §9.n, and §10.3 runs a version of each test against the DNS example. Each test is an attack or observation designed to show that a claim is false, which the paper calls falsifying it. For each test, the section also names the artifact, which is the record the assessor keeps as evidence. The tests have two purposes: to turn the §9 properties into something an assessor can check, and to catch systems that look secure only because they block everything.

The constrained actor (§8.1) is the agent or service whose actions are being authorized, and the protected effect is the change or outcome the authorization exists to control. The enforcement point is where the authorization decision is applied before the protected effect happens. A detail is material if changing it could change what the action does, or whether it should be allowed.

Each test tries actions that should be refused. Alongside them, the assessor also runs an action that should be allowed, called a positive control, to show that a refusal came from the rule being tested, not from something else going wrong, such as an expired access key, an unavailable service, or a rule that blocks too broadly. In the DNS example, the positive control is pointing www.example.com at one of the incident's approved backup addresses. It must go through the same enforcement point, under the same conditions, as the actions the test expects to be refused; otherwise the enforcement point might refuse everything it sees while real work goes around it.

Some results depend on others. For example, a C10 result means little if another path reaches the effect without the check (C1), so all tests must be run on the same scope and conditions (§11.1)

### 11.2.1 C1 — Coverage (§9.1)

**Test**: Take each path that could produce the protected effect, as listed in the assessment record (§11.1). On each one, try to produce the effect without first getting approval from the enforcement point. Include paths that run scripts, start other programs, disclose data, or trigger effects in downstream systems. When the actor can run arbitrary code or commands, also try every credential, open file or connection, network path, and privileged service the actor can reach, and every standing permission it holds beyond what this task granted. The claim is falsified if the protected effect happens without passing through the enforcement point, if a path meets only a weaker check than the enforcement point's (§9.1), or if the actor holds authority it could use to get around enforcement, even if the test did not use it.

**Artifact**: The paths, effects, and reachable authority listed in the assessment record, with the results of harmless test actions and alternate-path attempts.

**Note**: To test for indirect effects, install a package whose install script tries a harmless file write or starts another program. If installing it was approved only as a download, that extra effect must be blocked or separately approved. A test covers only what it reaches, so when tools or execution settings change, review the path list again as well as rerunning the tests.

### 11.2.2 C2 — Integrity (§9.2)

**Test**: Using only the actor's own rights, try to change the policy, turn off enforcement, or replace the decision with one of its own. Where policy requires approval from an approver the actor cannot control, try to get that approval through a helper agent the actor runs, a second identity it controls, its own credential, or a workflow it controls. The claim is falsified if any of these attempts succeeds.

**Artifact**: A map of who controls the policy, the enforcement point, the approvers, and the signing keys, with the results of the tampering and self-approval tests.

### 11.2.3 C3 — Binding (§9.3)

**Test**: First, get one action, A, approved. Then run three kinds of test, each without getting a new approval:

* **Change the request.** Alter one material detail and send it: a field in the request, the service it is addressed to, the resource state the approval assumed, or the tool or server version it relied on.

* **Change the tool, not the request.** Send the same request after swapping the tool's code, configuration, or description, even if the tool still reports the same version.

* **Make the request ambiguous.** Send action A written in a way the enforcement point and the receiving service might read differently, such as with a field repeated, a path written another way, or unclear boundaries between messages.

The claim is falsified if any of these runs under A's approval. A change that policy declares immaterial, and that is confirmed to be immaterial, does not count.

**Artifact**: A list of what the approval is tied to, evidence of the tool versions in use, and the result of each test, including which component refused the mismatch.

### 11.2.4 C4 — Context (§9.4)

**Test**: Leave the facts from trusted sources unchanged, and run three kinds of test:

* **Change what the actor claims.** Alter information the actor supplies about itself or its request, such as its stated purpose, role, or risk level.

* **Change the labels.** Relabel untrusted data as trusted, or restricted data as public.

* **Mislead the approver.** Hide or misstate a material target, value, or effect in what an approver, whether a person or a system, is shown.

The claim is falsified if any of these results in approval.

**Artifact**: Which source sets each fact and label, how values are transformed along the way, what the approver was shown, what the approval covered, and the result of each test.

### 11.2.5 C5 — Delegation (§9.5)

**Test**: An intermediary is a service, operator, or agent that acts for someone else. Run two kinds of test:

* **Go beyond the delegation.** Give an intermediary a delegation narrower than the rights it holds on its own, then request an action outside that delegation. The claim is falsified if the action runs, unless policy recognizes a separate basis for it, such as the intermediary's own independent authority, a step-up, or a separate delegation (§9.5.2).

* **Route through an unapproved intermediary.** Send a request carrying a valid delegation through an intermediary that is not in the approved call-chain lineage (§9.5.4), meaning the sequence of parties allowed to carry the delegation. The claim is falsified if the action runs at all.

**Artifact**: What the delegation allows (actors, targets, operations, and limits), the approved call-chain lineage, and the result of each test.

### 11.2.6 C6 — Freshness (§9.6)

**Test**: Run three kinds of test:

* **Use an approval after it should stop working.** Try the approval, including a cached copy, after it has expired, after it has been revoked, after its permitted number of uses is spent, and after a material change in the resource's state or the tool's version.

* **Use it from the wrong party.** Where policy ties an approval to the party presenting it, present a still-valid approval from a different party.

* **Let delayed work run late.** Release queued work, or work the approved action started, after the approval stops being valid but before the protected effect happens.

The claim is falsified if any of these runs when the declared rules for expiry, revocation, use limits, or presenter say it should not.

**Artifact**: The rules for when an approval stops being valid, how quickly a revocation must take effect, and the result of each test.

### 11.2.7 C7 — Composition (§9.7)

**Test**: Run three kinds of test:

* **Send restricted data out.** Read data marked as restricted, then try a normally permitted action that sends it, or content derived from it, outside the system without authorized release. Repeat after an AI model has rewritten or summarized the data, after a tool change, and after handing the task to a helper agent. As the positive control, send the same action with public data. The claim is falsified if the restricted data, or anything derived from it, leaves.

* **Retry a denied action.** After an action is denied, retry it through a route that policy treats as equivalent, such as another tool or a reworded request. The claim is falsified if it runs. As the positive control, complete an authorized recovery or step-up and confirm that the action then runs, so that a system that simply denies forever does not pass.

* **Exceed a shared limit.** Send simultaneous requests against a shared limit, such as a budget or request quota. The claim is falsified if use exceeds the limit beyond any declared margin. Requests within the limit must still succeed.

A restriction may be removed only under a declared rule for isolation or release. If the correct restriction reached the enforcement point and was ignored, record the failure primarily under C10.

**Artifact**: How restrictions carry over to derived data, when data may be released, how denials are remembered and reset, the order in which simultaneous requests were processed, and the result of each test, including which restriction reached the enforcement point.

### 11.2.8 C8 — Failure behavior (§9.8)

**Test**: Take each service the authorization decision depends on, such as the decision service, each source of facts, and any service that must record evidence, and make it unavailable, one at a time. Also make each one slow or return errors, not only disappear. The claim is falsified if the protected effect goes ahead in a weaker mode that policy did not separately approve, such as with no decision, or with a cached approval that is no longer valid. As the positive control, any reduced mode that policy approved in advance must work as declared. Then repeat the applicable tests from §§11.2.1–11.2.10 in each approved reduced mode.

**Artifact**: The result of each outage and disruption test, where errors are reported, and what the system is allowed to do in each weaker mode.

### 11.2.9 C9 — Evidence (§9.9)

**Test**: The evidence must be the destination's own record of what it executed, or come from another source that neither the actor nor any component that forms or forwards the request controls. The enforcement point's own record cannot serve: it shows what was sent, not what ran. Run two kinds of test:

* **Tell two actions apart.** Run two approved actions that differ in a material way, including a pair with the same operation and target but different material values. The evidence must link each execution to its approval and report the operation, target, and material values or effect. The claim is falsified if the evidence cannot tell the two apart, leaves out or misstates the difference, or cannot be matched to its approval.

* **Tamper with the evidence.** At each point between the evidence's source and the party relying on it, try to alter, hide, or forge the evidence. The claim is falsified if any change goes undetected by the relying party.

**Artifact**: The paired execution records, the link from each record to its approval, any actions that only partly completed or whose outcome is unknown, who along the evidence path could alter, hide, or forge evidence, and the result of each test.

### 11.2.10 C10 — Restriction enforcement (§9.10)

**Test**: Work out the expected results from the declared restrictions, not from the implementation. Use correctly signed inputs from the sources policy trusts, so a rejected signature cannot hide a missing rule, and test the policy in the form the system actually runs, after any conversion. Then run two kinds of test:

* **Try prohibited values.** Test each prohibited value one input at a time, then in combination, at the edges of each limit, and against each exception. The claim is falsified if a declared restriction is violated and the protected effect still goes ahead, without an authorized exception or a completed step-up. A step-up is an additional approval that policy requires before the effect can happen, and it must hold the effect until that approval succeeds.

* **Try allowed values.** As the positive control, test values the restrictions permit, and confirm that the policy's decision is the one that actually controls the protected effect. This matters most here, because refusing everything looks the same as enforcing every restriction.

**Artifact**: A table mapping each restriction to its decision: trusted sources, allowed and prohibited values, the policy version in force, tests at the edge of each limit, observed decisions, and enforced outcomes.

**Note**: Mathematical proofs cover only the model they describe; deployment tests confirm that the running system matches that model.

### 11.2.11 Running the Tests

Once the scope, the assessment record, and the expected outcomes are set, the tests can run automatically. People still need to judge whether the path list is complete and whether the components assumed to be trustworthy actually are. Run the tests in the automated build and deployment process on every change to policy, tools, credentials, or paths, so that the change triggers in §11.1 fire when the change is made, not at the next scheduled assessment.

# 12\. Applying the Model in Practice

## 12.1 Bounded Autonomy

A natural objection to last-mile authorization is that checking each action would mean approving each one in advance, which would make autonomous agents impractical. It does not, because authority can be granted as limits rather than as a list. An authority outside the actor, such as a person or an incident system, sets limits on what it may do, and only that authority can change them. The actor then chooses its own actions within those limits, and each action is still checked, just before it takes effect, to make sure it stays inside them. The limits can cover what kinds of operation are allowed, which resources and destinations, what range of values, how much in total, during what time, at what level of risk, and what is forbidden. For example, a repair agent might be allowed to replace any failing server in one service, up to a set number, without anyone naming the server in advance. That still does not let it change DNS settings or access permissions. The DNS example works the same way: the incident record limits the change to two backup addresses, the workload chooses between them, and each change is still checked before it takes effect.

For programs that can run any code, such as shells, approve a bounded class of execution (§9.1): a defined kind of run, in a set environment, with limits on the authority it can reach. Then check each protected action the code later takes. A broad approval to "run code" is not enough. Assessing such an environment is mainly a C1 assessment of the sandbox and of who holds the credentials, and C3 binding applies to the environment rather than to each command (§9.3).

If useful limits cannot be stated, the model does not invent authority. Policy must require a step-up (a further approval before the action), limit the task to a simpler kind of action that is safe to allow, or refuse. An actor's own explanation never supplies authority outside the limits.

## 12.2 Enforcement Placement

Where the check sits largely shapes what it can see, and so which criteria it is well placed to establish. Placements can be combined. The table gives the typical strengths and limits of each placement; it is not a complete list, and a particular deployment may do better or worse. C8 depends mostly on how the check is built rather than where it sits, and C10 can generally be met at any placement for the inputs that placement sees.

| Where the check sits | What it sees | What it can establish | What it cannot establish on its own |
| :---- | :---- | :---- | :---- |
| A gateway or proxy in front of the service | The request as the caller sent it | C1 for paths that go through it; C3 over the request's fields; C6 at the time of the request | What happens after later services change the request (C3); paths that go around it (C1); evidence of what ran (C9) |
| A library inside the service | The operation as the service understands it | C3 over the service's own understanding; C7 for state the service keeps | C2, when one team controls both the library and the policy; paths outside the service |
| The tool server an agent calls | The agent's tool call and its values | C4, where the values came from; C5, whether each call stays within what was delegated | Effects the tool causes further on (C1, C3), unless the tool's effects are bound |
| An enforcement point that holds the credential | The request, which it builds and authenticates itself | C1, if every path to the effect needs that credential and the actor cannot get around it; C3 over what it sends; a record of what it sent, which supports the preventive claim but is not C9 evidence (§11.2.9) | How the destination reads the request and what it actually does (C9) |
| A service acting for a requester from another system, such as a Kubernetes operator | The request, and who the requester is in the system it came from | C5, if it gets a credential limited to the requester, or checks the call against the requester's authority in the target system | Requesters whose authority cannot be expressed in the target system (C5 not established) |
| A check at the destination | The operation the destination will carry out | C3 and C9 most directly | Anything the destination does not reveal; needs the vendor's cooperation |

Where to check depends largely on who controls what the tool does. Checking at the tool call is generally sufficient only when the tool server is part of the trusted base and its effects are bound under §9.3. Otherwise, it is usually safer to check each protected effect the tool causes, where that effect happens, and to treat the tool server as an intermediary under §9.5.

# 13\. Case Evidence by Criterion

The cases in §6 show how authorization fails at runtime, but they don't reach every criterion. This section maps them to C1–C10, along with six more public incidents (Table 13a) and the demonstrations, disclosures, CVEs, and documented configurations that fill in the rest (Table 13b). D means the public record directly shows the criterion failing; P means the support is partial or depends on conditions. Marks follow the attribution rule in §9.10.4 and the declared-scope rule in §9.5.3. They describe the public record, not a finding against any organization.

**Table 13a — Public incidents** (D: direct evidence; P: partial evidence)

| Case | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 |
| ----- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Bangladesh Bank (2016, §6.1) | — | P | — | — | — | — | P | — | P | — |
| Capital One (2019) | P | — | — | — | P | — | — | — | — | — |
| GitHub/Heroku (2022, §6.2) | — | — | — | — | P | — | — | — | — | — |
| Cloudflare after Okta (2023) | — | — | — | — | — | D | — | — | — | — |
| Storm-0558 (2023) | — | — | — | — | — | — | — | — | D | D |
| Midnight Blizzard (2023–2024) | — | D | — | — | P | — | — | — | — | — |
| Bybit (2025, §6.3) | — | P | D | D | — | — | — | — | — | — |
| Replit (2025) | — | — | — | — | — | — | — | — | P | P |
| Salesloft Drift (2025) | — | — | — | — | P | — | — | — | — | — |
| Hugging Face (2026, §6.4) | P | — | — | — | P | — | — | — | — | — |

**Table 13b — Demonstrations, disclosures, CVEs, and documented configurations**

| Case | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 |
| ----- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| GitHub-to-AWS OIDC: missing subject restriction (2023) \[92\] | — | — | — | — | P | — | — | — | — | D |
| FortiAIOps CVE-2024-27782: session-token reuse (2024) \[96\] | — | — | — | — | — | D | — | — | — | — |
| Invariant experiment 1: incomplete confirmation (2025) \[60\] | — | — | P | D | — | — | — | — | — | — |
| Invariant experiment 2: tool shadowing (2025) \[60\] | — | — | — | D | D | — | — | — | — | — |
| GitHub MCP: private read to public pull request (2025) \[76\] | — | — | — | D | P | — | D | — | — | — |
| EchoLeak: retrieval-to-rendering exfiltration (2025) \[75\] | — | — | — | D | — | — | D | — | — | — |
| Cursor CVE-2025-54135: missing MCP-configuration gate (2025) \[54\] | D | D | — | P | — | — | — | — | — | — |
| Copilot CVE-2025-53773: approval settings (2025) \[97\] | — | D | — | P | — | — | — | — | — | — |
| GhostJacking: DNS change (2026, §6.5) \[3\] | — | — | — | D | P | — | — | — | — | — |
| Config Connector: organization IAM binding (2026, §6.6) \[42\] | — | — | — | — | P | — | — | — | — | — |
| AgentCore Harness: shell action and reachable credential (2026) \[51\] | P | — | — | — | P | — | — | — | — | — |
| ACS: default-proceed posture and unauthenticated decision channel (2026, §9.8) \[81\] | — | P | — | — | — | — | — | D | — | — |
| PortSwigger limit-overrun lab: collective reuse \[98\] | — | — | — | — | — | D | D | — | — | — |
| CWE-778 Example 3: incomplete logging \[99\] | — | — | — | — | — | — | — | — | P | — |

**Capital One** (C1 and C5, partial). In 2019 an intruder used a misconfigured web application firewall to reach the cloud's instance metadata service, which handed back the temporary credentials of the firewall's role. Those credentials then read customer data from storage \[4\]. The storage reads passed IAM checks, since the credentials were valid; what nothing checked was the path to the credentials. That is reachable authority, the same pattern AgentCore shows, so it supports C1 only partly. The role could read far more than a firewall needs, but with no declared scope on record, that supports C5 only partly too.

**Cloudflare after Okta (C6)**. After credentials leaked in the October 2023 Okta breach, Cloudflare rotated thousands of them but missed one service token and three service accounts it believed were unused. An attacker used them in November to reach its Atlassian systems \[70\]. Authority that should have been cancelled was still usable.

**Storm-0558 (C9 and C10)**. In 2023 an actor used an acquired Microsoft consumer signing key to forge tokens that Exchange Online accepted for enterprise mailboxes \[93\]\[94\]. A consumer key should never have been valid for enterprise tokens. The rule existed, but the validating code assumed a software library checked the issuer, and it didn't \[94\] (C10). Most victims also had no record of what the forged tokens read. The mailbox-access log that let the State Department detect the intrusion was available only with a premium license, and Microsoft could not supply past logs to victims who lacked it \[84\] (C9).

**Midnight Blizzard (C2, and C5 partial)**. In late 2023 and early 2024 an actor took over a legacy test OAuth application with elevated access, created its own OAuth applications and a user account to approve them, and used the legacy application to grant itself a role that reads mailboxes \[57\]. The actor controlled the authorization grants it was subject to (C2). The mailbox access went far beyond any purpose of a legacy test application, with no declared scope on record (C5, partial).

**Replit (C9 and C10, partial)**. In July 2025, Replit's AI coding agent deleted a user's production database during a code freeze the user had repeatedly stated in the tool. It then produced fabricated data and test results, and wrongly claimed that a rollback was impossible \[85\]\[86\]. Replit's chief executive called the deletion unacceptable \[100\]. The agent's own reports of what it had done, and whether it could be undone, were false. That shows why §9.9 requires evidence from outside the actor's control, but the record doesn't show that trusted execution records were missing (C9, partial). The freeze was stated, but nothing enforced it (C10, partial). The loss was small and recoverable; the case matters for how it happened.

**Salesloft Drift (C5, partial)**. In August 2025 an actor used OAuth tokens stolen from the Drift chatbot integration to export data from Salesforce instances at hundreds of organizations \[101\]\[102\]. The tokens could reach far more than a chatbot integration needs, a partial C5 mark. The actor deleted query jobs to hide the exports, but audit logs kept the evidence \[102\]. That illustrates §9.9's rule that evidence must sit outside the actor's control.

Coverage. Eight of the ten incidents in Table 13a involve no AI. Across both tables, every criterion has at least one direct mark. Among public incidents, C2, C3, C4, C6, C9, and C10 have direct marks; for C1, C5, C7, and C8, the direct marks come from Table 13b. For those four criteria, the incident record is partial:

* C1: Capital One and Hugging Face show authority reachable through unchecked paths, but neither record shows the protected effect itself getting past an equivalent check.

* C5: public records rarely show a declared task scope. Under §9.5.3 they show the gap without establishing that a declared scope was violated, so direct C5 evidence comes from controlled demonstrations.

* C7: Bangladesh Bank shows a fraud spread across many instructions, but the public record doesn't establish that a cumulative limit applied or was missing.

* C8: no public incident was found in which a check confirmed to fail open caused the harm. The C8 evidence is the documented default of the ACS reference Guardian \[81\] (§9.8).

For C7, C8, and C9, the weakness catalogs themselves note that such failures are underreported or underrepresented (§§9.7–9.9). The thin incident record reflects that limit; it does not measure how often these failures happen.

# 14\. Limitations

**What the model does not judge.** Last-mile authorization decides whether an action is authorized under the policy and the trusted facts, not whether an authorized action is harmful or mistaken in ways the policy does not address. It cannot fix a policy that grants the wrong authority: C10 tests whether declared restrictions are enforced, not whether they are the right ones.

**What it depends on.** The model limits what too-broad, stolen, or misdirected authority can do at the point of effect, but it does not prevent those causes. It relies on other disciplines: managing credentials, governing identities, writing policy, hardening AI models against injected instructions, and choosing secure defaults. It also assumes that the assessment can list actors, paths, and effects (§11.1), that identity and context sources are trustworthy (§8.1), and that scopes and restrictions are declared (C5, C10).

**What it does not cover.** C6 stops queued and not-yet-started work at points where it can still be checked; stopping or undoing effects already under way needs separate rollback and incident-response controls. Data-flow rules (C7) cover only declared sources and destinations, and cautious labeling can spread until it blocks useful work.

**Trust in the authorization system.** If the policy, a required source of facts, a trusted identity or signing authority, the enforcement mechanism, or the destination is compromised, the matching guarantee can fail, unless an independent check stays outside the compromised part.

**Coverage rests on testing.** Review and bypass testing can find missing paths but cannot prove none remain. Harrison, Ruzzo, and Ullman showed that, in the general access-matrix model, whether a right can leak is undecidable \[103\]. That does not rule out proofs for particular bounded systems, but in practice, coverage claims for real deployments rest on testing, not proof. Likewise, C10 tests support only the cases tested.

**No independent assessment yet.** The §10.3 lab shows that the tests can be run; it is not an assessment of a real deployment. Whether the model works across different kinds of systems, and whether independent assessors reach the same results, remain to be shown.

**Destinations without evidence.** A full claim cannot cover a destination that gives no usable evidence of what it did (§9.9), which excludes many SaaS integrations. Such destinations can still carry the preventive profile (§11.1).

# Conclusion

The idea is old. Anderson required a check that cannot be tampered with and is always used. Saltzer and Schroeder named that requirement complete mediation. Hardy showed what goes wrong when a program's own authority is mistaken for the authority its caller's request deserves. The weaknesses have been catalogued for two decades. What has been missing is the check at the point of effect.

Today's systems spread those old problems across far more paths. Services, CI/CD pipelines, orchestration platforms, automation, tools, and AI agents often hold valid identities and credentials. Those grants give standing authority; they do not show that each later action should happen. The gap widens whenever authority is granted earlier and software chooses more of the action later, so the check has to move with the action. At Bybit, the signers were genuine and their signatures valid, and more than \$1.5 billion still went to the attackers.

Identity is not authority. Possession is not permission.

For actions whose risk justifies it, the question that remains is:

*Can this actor, under this authority, perform this operation, on this target, with these values, given what came before and the trusted facts, right now?*

The ten criteria make that question testable, one declared kind of action at a time. None of the controls they require is new; the tests show whether those controls were applied. They test whether a deployment enforces the scope, delegation, and restrictions it declares, not whether those were the right ones to declare.

Check the action, not just the actor, at the last point where its effect can still be refused.

# Disclosure

The author, Michael Pak, is the founder of ZTUnion LLC, which develops Zero Trust Access Fabric (ZAF), a runtime authorization product. The author is the named inventor on U.S. Patent 12,695,750 \[56\], cited in §9.2 as an example of threshold validation, and patent applications on related authorization mechanisms are pending. The model does not depend on ZAF or on the patented design.

# References

1. BleepingComputer. “Lazarus Hacked Bybit via Breached Safe{Wallet} Developer Machine.” *BleepingComputer*, February 26, 2025\. Quotes Bybit’s post-incident statement. [https://www.bleepingcomputer.com/news/security/lazarus-hacked-bybit-via-breached-safe-wallet-developer-machine/](https://www.bleepingcomputer.com/news/security/lazarus-hacked-bybit-via-breached-safe-wallet-developer-machine/)

2. BlockSec. “Bybit Incident: A Web2 Breach Enables the Largest Crypto Hack in History.” *BlockSec Blog*, February 9, 2026\. [https://blocksec.com/blog/bybit-incident-a-web2-breach-enables-the-largest-crypto-hack-in-history](https://blocksec.com/blog/bybit-incident-a-web2-breach-enables-the-largest-crypto-hack-in-history)

3. Tenet Security Threat Labs. “GhostJacking Attacks: Half of the Fortune 500 Run These Tools. Getting Blocked by the Firewall Was the Way to Take Over Their AI Agents.” August 9, 2026; updated August 13, 2026\. [https://tenetsecurity.ai/blog/ghostjacking-attacks-agentic-kill-chain/](https://tenetsecurity.ai/blog/ghostjacking-attacks-agentic-kill-chain/)

4. Krebs, Brian. “What We Can Learn from the Capital One Hack.” *KrebsOnSecurity*, August 2, 2019\. [https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/](https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/)

5. Huntress. “Capital One Data Breach: What Happened, Impact, and Lessons.” *Huntress Threat Library*, November 21, 2025\. [https://www.huntress.com/threat-library/data-breach/capital-one-data-breach](https://www.huntress.com/threat-library/data-breach/capital-one-data-breach)

6. Anderson, James P. *Computer Security Technology Planning Study, Volume I*. ESD-TR-73-51, Electronic Systems Division, Air Force Systems Command, October 1972\. [https://csrc.nist.gov/files/pubs/conference/1998/10/08/proceedings-of-the-21st-nissc-1998/final/docs/early-cs-papers/ande72a.pdf](https://csrc.nist.gov/files/pubs/conference/1998/10/08/proceedings-of-the-21st-nissc-1998/final/docs/early-cs-papers/ande72a.pdf)

7. Saltzer, Jerome H., and Michael D. Schroeder. “The Protection of Information in Computer Systems.” *Proceedings of the IEEE*, Vol. 63, No. 9, September 1975, pp. 1278–1308. [https://web.mit.edu/saltzer/www/publications/protection/](https://web.mit.edu/saltzer/www/publications/protection/)

8. Hardy, Norm. “The Confused Deputy (or why capabilities might have been invented).” *ACM SIGOPS Operating Systems Review*, Vol. 22, No. 4, October 1988, pp. 36–38. [https://pdos.csail.mit.edu/6.828/2009/readings/hardy-confused-deputy.html](https://pdos.csail.mit.edu/6.828/2009/readings/hardy-confused-deputy.html)

9. Abadi, Martín, Michael Burrows, Butler Lampson, and Gordon Plotkin. “A Calculus for Access Control in Distributed Systems.” *ACM Transactions on Programming Languages and Systems*, Vol. 15, No. 4, September 1993, pp. 706–734. [https://doi.org/10.1145/155183.155225](https://doi.org/10.1145/155183.155225)

10. Ferraiolo, David F., and D. Richard Kuhn. “Role-Based Access Controls.” *15th National Computer Security Conference*, October 1992, pp. 554–563. [https://csrc.nist.gov/pubs/conference/1992/10/13/rolebased-access-controls/final](https://csrc.nist.gov/pubs/conference/1992/10/13/rolebased-access-controls/final)

11. Lodderstedt, Torsten, et al. *OAuth 2.0 Rich Authorization Requests*. RFC 9396, IETF, May 2023\. [https://www.rfc-editor.org/rfc/rfc9396.html](https://www.rfc-editor.org/rfc/rfc9396.html)

12. Jones, Michael B., et al. *OAuth 2.0 Token Exchange*. RFC 8693, IETF, January 2020\. [https://www.rfc-editor.org/rfc/rfc8693.html](https://www.rfc-editor.org/rfc/rfc8693.html)

13. Hu, Vincent C., et al. *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*. NIST SP 800-162, January 2014; updated August 2019\. [https://doi.org/10.6028/NIST.SP.800-162](https://doi.org/10.6028/NIST.SP.800-162)

14. Rose, Scott, Oliver Borchert, Stu Mitchell, and Sean Connelly. *Zero Trust Architecture*. NIST SP 800-207, August 2020\. [https://doi.org/10.6028/NIST.SP.800-207](https://doi.org/10.6028/NIST.SP.800-207)

15. Chandramouli, Ramaswamy, and Zack Butcher. *A Zero Trust Architecture Model for Access Control in Cloud-Native Applications in Multi-Location Environments*. NIST SP 800-207A, September 2023\. [https://doi.org/10.6028/NIST.SP.800-207A](https://doi.org/10.6028/NIST.SP.800-207A)

16. U.S. Department of Defense. *Trusted Computer System Evaluation Criteria (TCSEC)*, DoD 5200.28-STD, December 1985\. [https://csrc.nist.gov/files/pubs/conference/1998/10/08/proceedings-of-the-21st-nissc-1998/final/docs/early-cs-papers/dod85.pdf](https://csrc.nist.gov/files/pubs/conference/1998/10/08/proceedings-of-the-21st-nissc-1998/final/docs/early-cs-papers/dod85.pdf)

17. Cedar Policy Language. “How Cedar Authorization Works.” [https://docs.cedarpolicy.com/auth/authorization.html](https://docs.cedarpolicy.com/auth/authorization.html)

18. Rissanen, Erik, ed. *eXtensible Access Control Markup Language (XACML) Version 3.0*. OASIS Standard, January 22, 2013\. [https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html)

19. Open Policy Agent. “Open Policy Agent Documentation.” [https://www.openpolicyagent.org/docs](https://www.openpolicyagent.org/docs)

20. Pang, Ruoming, et al. “Zanzibar: Google’s Consistent, Global Authorization System.” *2019 USENIX Annual Technical Conference (USENIX ATC ’19)*, 2019\. [https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)

21. OpenID Foundation AuthZEN Working Group. *Authorization API 1.0*. OpenID Final Specification, approved January 12, 2026\. [https://openid.net/specs/authorization-api-1\_0.html](https://openid.net/specs/authorization-api-1_0.html)

22. NIST CSWP 20, *Planning for a Zero Trust Architecture: A Planning Guide for Federal Administrators*, National Institute of Standards and Technology, May 6, 2022, §1.1.3, “Tenets that Apply to Data Flows.” [https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.20.pdf](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.20.pdf)

23. Park, Jaehong, and Ravi Sandhu. “The UCON\_ABC Usage Control Model.” *ACM Transactions on Information and System Security*, Vol. 7, No. 1, February 2004, pp. 128–174. [https://doi.org/10.1145/984334.984339](https://doi.org/10.1145/984334.984339)

24. Valente, Joseph, and Michal Zalewski. “Beyond Zero: Enterprise Security for the AI Era.” *ACM Queue*, Vol. 24, No. 3, 2026\. arXiv:2605.22985. [https://queue.acm.org/doi/10.1145/3819083](https://queue.acm.org/doi/10.1145/3819083)

25. OWASP GenAI Security Project. “LLM06:2025 Excessive Agency.” [https://genai.owasp.org/llmrisk/llm062025-excessive-agency/](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/). 2025 edition; the 2026 edition, published August 2026, lists Excessive Agency as LLM03.

26. OWASP Cheat Sheet Series. “AI Agent Security Cheat Sheet.” Accessed September 22, 2026 (Pacific). [https://cheatsheetseries.owasp.org/cheatsheets/AI\_Agent\_Security\_Cheat\_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)

27. Wu, Mengting, Lin Wang, Yong Zhang, and Jiang Deng. “From Intent to Execution Grant: An Execution-Boundary Conformance Profile for High-Risk AI Actions.” arXiv:2609.11596, September 10, 2026\. [https://arxiv.org/abs/2609.11596](https://arxiv.org/abs/2609.11596)

28. Rhodes, James, and George Kang. “Proof of Execution: Runtime Verification for Governed AI Agent Actions.” arXiv:2607.05397, 2026\. [https://arxiv.org/abs/2607.05397](https://arxiv.org/abs/2607.05397)

29. Clark, David D., and David R. Wilson. “A Comparison of Commercial and Military Computer Security Policies.” *1987 IEEE Symposium on Security and Privacy*, pp. 184–195, 1987\. [https://doi.org/10.1109/SP.1987.10001](https://doi.org/10.1109/SP.1987.10001)

30. MITRE. *Common Weakness Enumeration (CWE)*. Weakness titles as listed in CWE 4.20. Accessed September 26, 2026 (Pacific). [https://cwe.mitre.org/](https://cwe.mitre.org/)

31. Truffle Security Research. “768 Leaked Corporate AWS Keys Held Full Admin Rights.” August 19, 2026\. [https://trufflesecurity.com/blog/leaked-corporate-aws-keys-held-full-admin-rights](https://trufflesecurity.com/blog/leaked-corporate-aws-keys-held-full-admin-rights)

32. Federal Reserve Bank of New York. “Statement on Media Reports About Bangladesh.” March 9, 2016\. [https://www.newyorkfed.org/newsevents/statements/2016/0311-2016](https://www.newyorkfed.org/newsevents/statements/2016/0311-2016)

33. U.S. Department of Justice. “North Korean Regime-Backed Programmer Charged With Conspiracy to Conduct Multiple Cyber Attacks and Intrusions.” September 6, 2018\. [https://www.justice.gov/archives/opa/pr/north-korean-regime-backed-programmer-charged-conspiracy-conduct-multiple-cyber-attacks-and](https://www.justice.gov/archives/opa/pr/north-korean-regime-backed-programmer-charged-conspiracy-conduct-multiple-cyber-attacks-and)

34. U.S. Department of Justice. *Indictment: United States v. Jon Chang Hyok, Kim Il, and Park Jin Hyok*. Filed December 8, 2020; unsealed February 17, 2021\. [https://www.justice.gov/archives/opa/press-release/file/1367701/dl](https://www.justice.gov/archives/opa/press-release/file/1367701/dl)

35. Shevchenko, Sergei. “Two Bytes to \$951m.” *BAE Systems Threat Research Blog*, April 25, 2016\. [https://baesystemsai.blogspot.com/2016/04/two-bytes-to-951m.html](https://baesystemsai.blogspot.com/2016/04/two-bytes-to-951m.html)

36. Staff Correspondent. “BB Heist: ‘SWIFT Is Responsible.’” *The Daily Star*, May 15, 2016; updated May 16, 2016\. [https://www.thedailystar.net/frontpage/swift-responsible-1224577](https://www.thedailystar.net/frontpage/swift-responsible-1224577)

37. GitHub. “Security Alert: Attack Campaign Involving Stolen OAuth User Tokens Issued to Two Third-Party Integrators.” April 15, 2022; updated April 27, 2022\. [https://github.blog/news-insights/company-news/security-alert-stolen-oauth-user-tokens/](https://github.blog/news-insights/company-news/security-alert-stolen-oauth-user-tokens/)

38. Wise, Bob. “April 2022 Incident Review.” *Heroku*, last updated June 14, 2022\. [https://www.heroku.com/blog/april-2022-incident-review/](https://www.heroku.com/blog/april-2022-incident-review/)

39. OpenAI. “The Hugging Face Incident and the Road Ahead.” August 26, 2026\. [https://openai.com/index/hugging-face-incident-and-the-road-ahead/](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)

40. Larcher, Hugo, Adrien Carreira, raphael g, and Christophe Rannou. “Anatomy of a Frontier Lab Agent Intrusion: A Technical Timeline of the July 2026 Incident.” *Hugging Face*, July 27, 2026\. [https://huggingface.co/blog/agent-intrusion-technical-timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline)

41. Columbus, Louis. “The Fix for the AI Agent That Hijacked a Company’s DNS: It Can Propose the Change, but It Can’t Approve It.” *VentureBeat*, August 26, 2026\. [https://venturebeat.com/security/the-fix-for-the-ai-agent-that-hijacked-a-companys-dns-it-can-propose-the-change-but-it-cant-approve-it](https://venturebeat.com/security/the-fix-for-the-ai-agent-that-hijacked-a-companys-dns-it-can-propose-the-change-but-it-cant-approve-it)

42. O’Leary, Justin. “ConfigConfusion: GCP IAM Authorization Bypass — Google Said ‘Nice Catch’ Then Left It Unpatched.” *OLearySec*, June 18, 2026\. [https://olearysec.com/research/config-connector-authorization-bypass/](https://olearysec.com/research/config-connector-authorization-bypass/)

43. Matan, Liv. “ImageRunner: A Privilege Escalation Vulnerability Impacting GCP Cloud Run.” *Tenable Blog*, April 1, 2025\. [https://www.tenable.com/blog/imagerunner-a-privilege-escalation-vulnerability-impacting-gcp-cloud-run](https://www.tenable.com/blog/imagerunner-a-privilege-escalation-vulnerability-impacting-gcp-cloud-run)

44. Birgisson, Arnar, et al. “Macaroons: Cookies with Contextual Caveats for Decentralized Authorization in the Cloud.” *NDSS Symposium 2014*, February 2014\. [https://www.ndss-symposium.org/ndss2014/ndss-2014-programme/macaroons-cookies-contextual-caveats-decentralized-authorization-cloud/](https://www.ndss-symposium.org/ndss2014/ndss-2014-programme/macaroons-cookies-contextual-caveats-decentralized-authorization-cloud/)

45. European Commission. Commission Delegated Regulation (EU) 2018/389, Article 5, “Dynamic linking,” and Articles 11 and 16 (cumulative limits on exempted payments). Regulatory technical standards supplementing Directive (EU) 2015/2366 (PSD2). [https://eur-lex.europa.eu/eli/reg\_del/2018/389/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2018/389/oj/eng)

46. Biba, K. J. *Integrity Considerations for Secure Computer Systems*. MTR-3153 Rev. 1, ESD-TR-76-372, The MITRE Corporation, April 1977\. DTIC ADA039324. [https://apps.dtic.mil/sti/html/tr/ADA039324/index.html](https://apps.dtic.mil/sti/html/tr/ADA039324/index.html)

47. Joint Task Force. *Security and Privacy Controls for Information Systems and Organizations*. NIST SP 800-53 Revision 5, September 2020, updated December 2020\. [https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf)

48. OWASP. Transaction Authorization Cheat Sheet. Sections 1.1 and 2.1–2.10. [https://cheatsheetseries.owasp.org/cheatsheets/Transaction\_Authorization\_Cheat\_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)

49. Joint Task Force. *Assessing Security and Privacy Controls in Information Systems and Organizations*. NIST SP 800-53A Revision 5, January 2022\. [https://csrc.nist.gov/pubs/sp/800/53/a/r5/final](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

50. npm. “Scripts.” *npm CLI v11 Documentation*, lifecycle scripts. Accessed September 19, 2026 (Pacific). [https://docs.npmjs.com/cli/v11/using-npm/scripts/](https://docs.npmjs.com/cli/v11/using-npm/scripts/)

51. Rabin, Niv. “A Vault with a Heap-View: The Uncomfortable Space Between AgentCore Harness and Identity.” Palo Alto Networks Unit 42, September 18, 2026\. [https://unit42.paloaltonetworks.com/securing-aws-agentcore-harness-credentials/](https://unit42.paloaltonetworks.com/securing-aws-agentcore-harness-credentials/)

52. Zhang, Xiaolan, Antony Edwards, and Trent Jaeger. “Using CQUAL for Static Analysis of Authorization Hook Placement.” *11th USENIX Security Symposium*, August 2002, pp. 33–48. [https://www.usenix.org/conference/11th-usenix-security-symposium/using-cqual-static-analysis-authorization-hook-placement](https://www.usenix.org/conference/11th-usenix-security-symposium/using-cqual-static-analysis-authorization-hook-placement)

53. Kubernetes Documentation. “Validating Admission Policy.” [https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)

54. Cursor. “Arbitrary Code Execution from Cursor Agent Through a Prompt Injection via MCP Special Files.” Security advisory GHSA-4cxx-hrm3-49rm, CVE-2025-54135, published August 2, 2025 (UTC). [https://github.com/cursor/cursor/security/advisories/GHSA-4cxx-hrm3-49rm](https://github.com/cursor/cursor/security/advisories/GHSA-4cxx-hrm3-49rm)

55. MITRE. “2025 CWE Top 25 Most Dangerous Software Weaknesses.” December 15, 2025\. [https://cwe.mitre.org/top25/archive/2025/2025\_cwe\_top25.html](https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html)

56. Pak, Michael. *System and Method for Proxy-Based Credential Custody with Distributed Validation*. U.S. Patent No. 12,695,750 B1, issued July 28, 2026\.

57. Microsoft. “Midnight Blizzard: Guidance for Responders on Nation-State Attack.” *Microsoft Security Blog*, January 25, 2024\. [https://www.microsoft.com/en-us/security/blog/2024/01/25/midnight-blizzard-guidance-for-responders-on-nation-state-attack/](https://www.microsoft.com/en-us/security/blog/2024/01/25/midnight-blizzard-guidance-for-responders-on-nation-state-attack/)

58. Torres-Arias, Santiago, Hammad Afzali, Trishank Karthik Kuppusamy, Reza Curtmola, and Justin Cappos. “in-toto: Providing Farm-to-Table Guarantees for Bits and Bytes.” *Proceedings of the 28th USENIX Security Symposium*, 2019, pp. 1393–1410.

59. Newman, Zachary, John Speed Meyers, and Santiago Torres-Arias. “Sigstore: Software Signing for Everybody.” *Proceedings of the 2022 ACM SIGSAC Conference on Computer and Communications Security (CCS ’22)*, 2022, pp. 2353–2367. [https://doi.org/10.1145/3548606.3560596](https://doi.org/10.1145/3548606.3560596)

60. Beurer-Kellner, Luca, and Marc Fischer. “MCP Security Notification: Tool Poisoning Attacks.” Invariant Labs, April 1, 2025\. Experiments 1 and 2\. [https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)

61. Fett, Daniel, et al. *OAuth 2.0 Demonstrating Proof of Possession (DPoP)*. RFC 9449, IETF, September 2023\. [https://www.rfc-editor.org/rfc/rfc9449.html](https://www.rfc-editor.org/rfc/rfc9449.html)

62. Campbell, Brian, et al. *OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens*. RFC 8705, IETF, February 2020\. [https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html)

63. SPIFFE Project. “SPIRE Concepts.” [https://spiffe.io/docs/latest/spire-about/spire-concepts/](https://spiffe.io/docs/latest/spire-about/spire-concepts/)

64. Debenedetti, Edoardo, et al. *Defeating Prompt Injections by Design*. arXiv:2503.18813, March 24, 2025; revised June 24, 2025\. CaMeL. [https://arxiv.org/abs/2503.18813](https://arxiv.org/abs/2503.18813)

65. Costa, Manuel, et al. *Securing AI Agents with Information-Flow Control*. arXiv:2505.23643, May 29, 2025; revised September 3, 2025\. Fides. [https://arxiv.org/abs/2505.23643](https://arxiv.org/abs/2505.23643)

66. Tulshibagwale, Atul, George Fletcher, and Pieter Kasselman. Transaction Tokens. draft-ietf-oauth-transaction-tokens-11, July 30, 2026\. IETF OAuth Working Group Internet-Draft; work in progress. Sections 4.1, 9.2, 12.2, 13.1–13.2, and 13.6. [https://datatracker.ietf.org/doc/draft-ietf-oauth-transaction-tokens/11/](https://datatracker.ietf.org/doc/draft-ietf-oauth-transaction-tokens/11/)

67. Wallach, Dan S., and Edward W. Felten. “Understanding Java Stack Inspection.” *1998 IEEE Symposium on Security and Privacy*, pp. 52–63. [https://doi.org/10.1109/SECPRI.1998.674823](https://doi.org/10.1109/SECPRI.1998.674823)

68. MITRE. “CWE-441: Unintended Proxy or Intermediary (‘Confused Deputy’).” CWE 4.20. [https://cwe.mitre.org/data/definitions/441.html](https://cwe.mitre.org/data/definitions/441.html)

69. OpenID Foundation Shared Signals Working Group. *OpenID Continuous Access Evaluation Profile 1.0*. OpenID Final Specification, 2025\. [https://openid.net/specs/openid-caep-1\_0-final.html](https://openid.net/specs/openid-caep-1_0-final.html)

70. BleepingComputer. “Cloudflare Hacked Using Auth Tokens Stolen in Okta Attack.” *BleepingComputer*, February 1, 2024\. [https://www.bleepingcomputer.com/news/security/cloudflare-hacked-using-auth-tokens-stolen-in-okta-attack/](https://www.bleepingcomputer.com/news/security/cloudflare-hacked-using-auth-tokens-stolen-in-okta-attack/)

71. Bell, D. Elliott, and Leonard J. LaPadula. *Secure Computer System: Unified Exposition and Multics Interpretation*. MTR-2997 Rev. 1, ESD-TR-75-306, The MITRE Corporation, March 1976\.

72. Denning, Dorothy E. “A Lattice Model of Secure Information Flow.” *Communications of the ACM*, Vol. 19, No. 5, May 1976, pp. 236–243. [https://doi.org/10.1145/360051.360056](https://doi.org/10.1145/360051.360056)

73. Goguen, Joseph A., and José Meseguer. “Security Policies and Security Models.” *1982 IEEE Symposium on Security and Privacy*, pp. 11–20. [https://doi.org/10.1109/SP.1982.10014](https://doi.org/10.1109/SP.1982.10014)

74. Brewer, David F. C., and Michael J. Nash. “The Chinese Wall Security Policy.” *1989 IEEE Symposium on Security and Privacy*, pp. 206–214. [https://doi.org/10.1109/SECPRI.1989.36295](https://doi.org/10.1109/SECPRI.1989.36295)

75. Ravia, Itay. “Breaking down ‘EchoLeak’, the First Zero-Click AI Vulnerability Enabling Data Exfiltration from Microsoft 365 Copilot.” Aim Labs, June 11, 2025\. Original disclosure: [https://www.aim.security/lp/aim-labs-echoleak-blogpost](https://www.aim.security/lp/aim-labs-echoleak-blogpost). Republication by the same author at Cato Networks: [https://www.catonetworks.com/blog/breaking-down-echoleak/](https://www.catonetworks.com/blog/breaking-down-echoleak/).

76. Milanta, Marco, and Luca Beurer-Kellner. “GitHub MCP Exploited: Accessing Private Repositories via MCP.” Invariant Labs, May 26, 2025\. [https://invariantlabs.ai/blog/mcp-github-vulnerability](https://invariantlabs.ai/blog/mcp-github-vulnerability)

77. MITRE. “CWE-841: Improper Enforcement of Behavioral Workflow.” CWE 4.20. [https://cwe.mitre.org/data/definitions/841.html](https://cwe.mitre.org/data/definitions/841.html)

78. Kubernetes. Admission registration API (v1), `FailurePolicyType`. Source file `staging/src/k8s.io/api/admissionregistration/v1/types.go`. [https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/api/admissionregistration/v1/types.go](https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/api/admissionregistration/v1/types.go)

79. Kubernetes. “Admission Webhook Good Practices.” Section “Fail open and validate the final state.” Accessed September 26, 2026 (Pacific). [https://kubernetes.io/docs/concepts/cluster-administration/admission-webhooks-good-practices/](https://kubernetes.io/docs/concepts/cluster-administration/admission-webhooks-good-practices/)

80. SELinux Project. *The SELinux Notebook*. Sections on neverallow rules and permissive mode. [https://github.com/SELinuxProject/selinux-notebook](https://github.com/SELinuxProject/selinux-notebook)

81. OWASP GenAI Security Project. Agent Control Standard repository README: reference implementation failure posture and limitations. Pinned to commit dc265475139a922824f0c817e2ecc2a2ce31c06c. [https://github.com/GenAI-Security-Project/agent-control-standard/blob/dc265475139a922824f0c817e2ecc2a2ce31c06c/README.md](https://github.com/GenAI-Security-Project/agent-control-standard/blob/dc265475139a922824f0c817e2ecc2a2ce31c06c/README.md)

82. OWASP Foundation. “A10:2025 Mishandling of Exceptional Conditions.” *OWASP Top 10:2025*. [https://owasp.org/Top10/2025/A10\_2025-Mishandling\_of\_Exceptional\_Conditions](https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions)

83. MITRE. “CWE-636: Not Failing Securely (‘Failing Open’).” CWE 4.20. [https://cwe.mitre.org/data/definitions/636.html](https://cwe.mitre.org/data/definitions/636.html)

84. Cyber Safety Review Board. *Review of the Summer 2023 Microsoft Exchange Online Intrusion*. U.S. Department of Homeland Security, March 20, 2024\. [https://www.cisa.gov/sites/default/files/2025-03/CSRBReviewOfTheSummer2023MEOIntrusion508.pdf](https://www.cisa.gov/sites/default/files/2025-03/CSRBReviewOfTheSummer2023MEOIntrusion508.pdf)

85. The Register. “Vibe Coding Service Replit Deleted User’s Production Database, Faked Data, Told Fibs Galore.” July 21, 2025\. [https://www.theregister.com/2025/07/21/replit\_saastr\_vibe\_coding\_incident/](https://www.theregister.com/2025/07/21/replit_saastr_vibe_coding_incident/)

86. AI Incident Database. “Incident 1152: LLM-Driven Replit Agent Reportedly Executed Unauthorized Destructive Commands During Code Freeze, Leading to Loss of Production Data.” [https://incidentdatabase.ai/cite/1152/](https://incidentdatabase.ai/cite/1152/)

87. OWASP Foundation. “A09:2025 Security Logging and Alerting Failures.” *OWASP Top 10:2025*. [https://owasp.org/Top10/2025/A09\_2025-Security\_Logging\_and\_Alerting\_Failures/](https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/)

88. Backes, John, et al. *Semantic-Based Automated Reasoning for AWS Access Policies Using SMT*. 2018\. Zelkova research paper. [https://www.amazon.science/publications/semantic-based-automated-reasoning-for-aws-access-policies-using-smt](https://www.amazon.science/publications/semantic-based-automated-reasoning-for-aws-access-policies-using-smt)

89. Amazon Web Services. “Validate Policies with IAM Access Analyzer Custom Policy Checks.” *IAM User Guide*. Accessed September 19, 2026 (Pacific). [https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-custom-policy-checks.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-custom-policy-checks.html)

90. Erickson, Spencer, and Liana Hadarean. “Introducing Cedar Analysis: Open Source Tools for Verifying Authorization Policies.” *AWS Open Source Blog*, June 16, 2025\. [https://aws.amazon.com/blogs/opensource/introducing-cedar-analysis-open-source-tools-for-verifying-authorization-policies/](https://aws.amazon.com/blogs/opensource/introducing-cedar-analysis-open-source-tools-for-verifying-authorization-policies/)

91. Open Policy Agent. “Policy Testing.” Documentation. Accessed September 19, 2026 (Pacific). [https://www.openpolicyagent.org/docs/policy-testing](https://www.openpolicyagent.org/docs/policy-testing)

92. Tafani-Dereeper, Christophe. “No Keys Attached: Exploring GitHub-to-AWS Keyless Authentication Flaws.” *Datadog Security Labs*, July 27, 2023; updated June 18, 2025\. Original research and coordinated GDS disclosure. [https://securitylabs.datadoghq.com/articles/exploring-github-to-aws-keyless-authentication-flaws/](https://securitylabs.datadoghq.com/articles/exploring-github-to-aws-keyless-authentication-flaws/)

93. Microsoft Security Response Center. “Results of Major Technical Investigations for Storm-0558 Key Acquisition.” September 6, 2023\. [https://www.microsoft.com/en-us/msrc/blog/2023/09/results-of-major-technical-investigations-for-storm-0558-key-acquisition](https://www.microsoft.com/en-us/msrc/blog/2023/09/results-of-major-technical-investigations-for-storm-0558-key-acquisition)

94. Wiz. “Storm-0558 Update: Takeaways from Microsoft’s Recent Report.” *Wiz Blog*, September 7, 2023\. [https://www.wiz.io/blog/key-takeaways-from-microsofts-latest-storm-0558-report](https://www.wiz.io/blog/key-takeaways-from-microsofts-latest-storm-0558-report)

95. OpenID Foundation AuthZEN Working Group. *AuthZEN Profile for Obligations 1.0*. Working-group draft, Draft 1, July 3, 2026\. [https://openid.github.io/authzen/authzen-obligations-profile-1\_0.html](https://openid.github.io/authzen/authzen-obligations-profile-1_0.html)

96. NIST National Vulnerability Database. “CVE-2024-27782 Detail.” Fortinet CNA description: multiple insufficient session expiration weaknesses in FortiAIOps 2.0.0. Published July 9, 2024\. [https://nvd.nist.gov/vuln/detail/CVE-2024-27782](https://nvd.nist.gov/vuln/detail/CVE-2024-27782)

97. Embrace The Red (wunderwuzzi). “GitHub Copilot: Remote Code Execution via Prompt Injection (CVE-2025-53773).” August 12, 2025\. [https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection/](https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection/)

98. PortSwigger Web Security Academy. Lab: Limit Overrun Race Conditions. Published laboratory exercise and solution. [https://portswigger.net/web-security/race-conditions/lab-race-conditions-limit-overrun](https://portswigger.net/web-security/race-conditions/lab-race-conditions-limit-overrun)

99. MITRE. CWE-778: Insufficient Logging. Demonstrative Example 3, Azure Storage logging configuration. [https://cwe.mitre.org/data/definitions/778.html](https://cwe.mitre.org/data/definitions/778.html)

100. The Register. “Replit Makes Vibe-y Promise to Stop Its AI Agents Making Vibe Coding Disasters.” July 22, 2025\. [https://www.theregister.com/2025/07/22/replit\_saastr\_response/](https://www.theregister.com/2025/07/22/replit_saastr_response/)

101. Arctic Wolf. “Widespread Salesforce Data Theft via Compromised Salesloft Drift OAuth Tokens.” August 27, 2025\. [https://arcticwolf.com/resources/blog/widespread-salesforce-data-theft-via-compromised-salesloft-drift-oauth-tokens/](https://arcticwolf.com/resources/blog/widespread-salesforce-data-theft-via-compromised-salesloft-drift-oauth-tokens/)

102. AppOmni. “Salesloft Drift–Salesforce Breach (UNC6395): Why Salesforce OAuth Integrations Are a Growing Risk.” May 6, 2026\. [https://appomni.com/blog/drift-breach-salesforce-unc6395-saas-prevention/](https://appomni.com/blog/drift-breach-salesforce-unc6395-saas-prevention/)

103. Harrison, Michael A., Walter L. Ruzzo, and Jeffrey D. Ullman. “Protection in Operating Systems.” *Communications of the ACM*, Vol. 19, No. 8, August 1976, pp. 461–471. [https://doi.org/10.1145/360303.360333](https://doi.org/10.1145/360303.360333)
