package documents
import rego.v1
default scope_ok := false
default rar_ok := false
default provider_ok := false
scope_ok if { concat("", ["document.",input.action]) in split(input.scope," ") }
rar_ok if { input.rar_present == false }
rar_ok if {
 input.rar_present
 input.rar_valid
 some grant in input.authorization_details
 grant.identifier == input.resource.id
 input.action in grant.actions
}
provider_ok if {
 input.subject == input.resource.owner
 input.action == "read"
}
provider_ok if {
 input.subject == input.resource.owner
 input.action == "update"
 input.resource.locked == false
}
default allow := false
allow if { scope_ok; rar_ok; provider_ok }
reasons contains "scope_missing" if { not scope_ok }
reasons contains "rar_out_of_bounds" if { not rar_ok }
reasons contains "provider_policy_denied" if { not provider_ok }
decision := {"allow":allow,"checks":{"scope":scope_ok,"rar":rar_ok,"provider":provider_ok},"reasons":sort(reasons),"policy_version":"documents-v1"}
