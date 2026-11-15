package local.rarlab;
import org.keycloak.authentication.*;
import org.keycloak.models.*;
public final class Consent implements Authenticator{
 public void authenticate(AuthenticationFlowContext c){
  var raw=c.getAuthenticationSession().getClientNote(Profile.NOTE);
  if(raw==null){c.failure(AuthenticationFlowError.INTERNAL_ERROR);return;}
  try{
   var form=c.form().setAttribute("rarMode",!raw.isBlank()).setAttribute("requestJson",raw.isBlank()?"scope=document.read document.update":raw);
   if(!raw.isBlank()){
    var detail=Profile.parse(raw).get(0);form.setAttribute("documentId",detail.get("identifier"));form.setAttribute("operations",String.join(" / ",(java.util.List<String>)detail.get("actions")));
   }
   c.challenge(form.createForm("rar-consent.ftl"));
  }catch(Exception e){c.failure(AuthenticationFlowError.INTERNAL_ERROR);}
 }
 public void action(AuthenticationFlowContext c){
  if(!"yes".equals(c.getHttpRequest().getDecodedFormParameters().getFirst("approve"))){c.cancelLogin();return;}
  c.getAuthenticationSession().setClientNote(Profile.APPROVED,"yes");c.success();
 }
 public boolean requiresUser(){return true;}public boolean configuredFor(KeycloakSession s,RealmModel r,UserModel u){return true;}
 public void setRequiredActions(KeycloakSession s,RealmModel r,UserModel u){}public void close(){}
}
