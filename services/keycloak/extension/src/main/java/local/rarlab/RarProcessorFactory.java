package local.rarlab;
import org.keycloak.Config;
import org.keycloak.models.KeycloakSession;
import org.keycloak.protocol.oidc.rar.*;
import org.keycloak.representations.AuthorizationDetailsJSONRepresentation;
public final class RarProcessorFactory implements AuthorizationDetailsProcessorFactory {
 public String getId(){return Profile.TYPE;}
 public AuthorizationDetailsProcessor<?> create(KeycloakSession s){return new RarProcessor();}
 public void init(Config.Scope c){org.keycloak.util.AuthorizationDetailsParser.registerParser(Profile.TYPE,new org.keycloak.util.AuthorizationDetailsParser(){
  public <T extends AuthorizationDetailsJSONRepresentation>T asSubtype(AuthorizationDetailsJSONRepresentation d,Class<T> type){return type.cast(d);}
 });}
}
