package local.rarlab;
import java.util.List;
import org.keycloak.models.*;
import org.keycloak.protocol.oidc.mappers.*;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.representations.*;
public final class GrantMapper extends AbstractOIDCProtocolMapper implements OIDCAccessTokenMapper {
 public String getId(){return "rar-lab-grant";}public String getDisplayType(){return "RAR Lab grant";}
 public String getDisplayCategory(){return TOKEN_MAPPER_CATEGORY;}public String getHelpText(){return "Emit the consent-bound RAR grant.";}
 public List<ProviderConfigProperty> getConfigProperties(){return List.of();}
 protected void setClaim(IDToken token,ProtocolMapperModel m,UserSessionModel u,KeycloakSession s,ClientSessionContext c){
  if(!"yes".equals(c.getClientSession().getNote(Profile.APPROVED)))throw new IllegalArgumentException("No consent");
  String raw=c.getClientSession().getNote(Profile.NOTE);if(raw==null||raw.isBlank())return;
  try{((AccessToken)token).setAuthorizationDetails(List.of(Profile.representation(raw)));}catch(Exception e){throw new IllegalArgumentException("Invalid grant");}
 }
}
