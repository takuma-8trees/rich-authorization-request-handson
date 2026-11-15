package documents_test
import rego.v1
import data.documents.decision
base := {"subject":"alice","scope":"document.read document.update","rar_present":true,"rar_valid":true,"authorization_details":[{"identifier":"doc-a","actions":["read","update"]}],"action":"update","resource":{"id":"doc-a","owner":"alice","locked":false}}
test_match if { d := decision with input as base; d.allow }
test_wrong_document if { d := decision with input as object.union(base,{"resource":{"id":"doc-b"}}); not d.allow }
test_locked if { d := decision with input as object.union(base,{"resource":{"locked":true}}); not d.allow }
test_wrong_owner if { d := decision with input as object.union(base,{"resource":{"owner":"bob"}}); not d.allow }
test_no_scope if { d := decision with input as object.union(base,{"scope":"openid"}); not d.allow }
test_invalid_rar if { d := decision with input as object.union(base,{"rar_valid":false}); not d.allow }
test_scope_baseline if { d := decision with input as object.union(base,{"rar_present":false,"resource":{"id":"doc-b"}}); d.allow }
