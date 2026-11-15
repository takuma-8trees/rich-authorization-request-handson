package local.rarlab;
import org.keycloak.models.KeycloakSession;
import org.keycloak.representations.idm.ClientPolicyExecutorConfigurationRepresentation;
import org.keycloak.services.clientpolicy.*;
import org.keycloak.services.clientpolicy.context.AuthorizationRequestContext;
import org.keycloak.services.clientpolicy.executor.ClientPolicyExecutorProvider;
public final class RequestPolicy implements ClientPolicyExecutorProvider<ClientPolicyExecutorConfigurationRepresentation>{
 public String getProviderId(){return "rar-lab-policy";}
 public void setupConfiguration(ClientPolicyExecutorConfigurationRepresentation c){}
 public void executeOnEvent(ClientPolicyContext c)throws ClientPolicyException{
  if(c.getEvent()!=ClientPolicyEvent.AUTHORIZATION_REQUEST)return;
  var r=(AuthorizationRequestContext)c;if(!r.getClient().getClientId().equals("rar-browser"))return;
  try{
   var params=r.getRequestParameters();var raw=params.getFirst("authorization_details");
   if(raw!=null&&params.get("authorization_details").size()!=1)throw new IllegalArgumentException();
   var note=raw==null?"":Profile.json(Profile.parse(raw));
   r.getAuthenticationSession().setClientNote(Profile.NOTE,note);
   r.getAuthenticationSession().setClientNote(Profile.APPROVED,"");
  }catch(Exception e){throw new ClientPolicyException("invalid_authorization_details","Unsupported document authorization details");}
 }
}
