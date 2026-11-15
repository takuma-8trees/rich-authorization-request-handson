package local.rarlab;
import java.util.*;
import org.keycloak.representations.AuthorizationDetailsJSONRepresentation;
import org.keycloak.util.JsonSerialization;

/** Closed teaching profile; not a standardized document permission vocabulary. */
public final class Profile {
 public static final String TYPE="urn:rar-lab:document-access:v1", NOTE="rar_lab_request", APPROVED="rar_lab_approved";
 public static final String LOCATION="http://localhost:18770/documents";
 public static List<Map<String,Object>> parse(String raw) throws Exception {
  if(raw==null||raw.length()>2048)throw new IllegalArgumentException("Missing or oversized RAR");
  Object value=JsonSerialization.readValue(raw,Object.class);
  if(!(value instanceof List<?> list)||list.size()!=1||!(list.get(0) instanceof Map<?,?> item)
   ||!item.keySet().equals(Set.of("type","actions","locations","identifier"))||!TYPE.equals(item.get("type"))
   ||!List.of(LOCATION).equals(item.get("locations"))||!Set.of("doc-a","doc-b").contains(item.get("identifier"))
   ||!(item.get("actions") instanceof List<?> actions)||actions.isEmpty()||actions.size()!=new HashSet<>(actions).size()
   ||!Set.of("read","update").containsAll(actions))throw new IllegalArgumentException("Unsupported RAR");
  return List.of(Map.of("type",TYPE,"actions",actions.stream().map(String.class::cast).sorted().toList(),"locations",List.of(LOCATION),"identifier",item.get("identifier")));
 }
 public static AuthorizationDetailsJSONRepresentation representation(String raw) throws Exception {
  var item=parse(raw).get(0);var result=new AuthorizationDetailsJSONRepresentation();
  result.setType(TYPE);result.setIdentifier((String)item.get("identifier"));result.setLocations(List.of(LOCATION));
  result.setActions(((List<?>)item.get("actions")).stream().map(String.class::cast).toList());return result;
 }
 public static String json(Object value) throws Exception {return JsonSerialization.writeValueAsString(value);}
 public static String json(AuthorizationDetailsJSONRepresentation d) throws Exception {
  if(d.getDatatypes()!=null||d.getPrivileges()!=null||!d.getCustomData().isEmpty())throw new IllegalArgumentException("Unknown RAR fields");
  return json(List.of(Map.of("type",d.getType(),"identifier",d.getIdentifier(),"actions",d.getActions(),"locations",d.getLocations())));
 }
}
