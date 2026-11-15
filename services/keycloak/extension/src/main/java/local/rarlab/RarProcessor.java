package local.rarlab;
import java.util.List;
import org.keycloak.models.*;
import org.keycloak.protocol.oidc.rar.*;
import org.keycloak.representations.AuthorizationDetailsJSONRepresentation;
public final class RarProcessor implements AuthorizationDetailsProcessor<AuthorizationDetailsJSONRepresentation>{
 public boolean isSupported(){return true;}
 public String getSupportedType(){return Profile.TYPE;}
 public Class<AuthorizationDetailsJSONRepresentation> getSupportedResponseJavaType(){return AuthorizationDetailsJSONRepresentation.class;}
 public AuthorizationDetailsJSONRepresentation validateAuthorizationDetail(AuthorizationDetailsJSONRepresentation d){
  try{return Profile.representation(Profile.json(d));}catch(Exception e){throw new InvalidAuthorizationDetailsException("Unsupported document RAR");}
 }
 public AuthorizationDetailsJSONRepresentation process(UserSessionModel u,ClientSessionContext c,AuthorizationDetailsJSONRepresentation d){
  try{
   if(!"rar-browser".equals(c.getClientSession().getClient().getClientId()))throw new IllegalArgumentException();
   String raw=c.getClientSession().getNote(Profile.NOTE);
   if(!"yes".equals(c.getClientSession().getNote(Profile.APPROVED))||!Profile.parse(raw).equals(Profile.parse(Profile.json(d))))throw new IllegalArgumentException();
   return Profile.representation(raw);
  }catch(Exception e){throw new InvalidAuthorizationDetailsException("RAR differs from approved grant");}
 }
 public AuthorizationDetailsJSONRepresentation processStoredAuthorizationDetails(UserSessionModel u,ClientSessionContext c,AuthorizationDetailsJSONRepresentation d){return process(u,c,d);}
 public List<AuthorizationDetailsJSONRepresentation> handleMissingAuthorizationDetails(UserSessionModel u,ClientSessionContext c){
  String raw=c.getClientSession().getNote(Profile.NOTE);if(raw==null||raw.isBlank())return List.of();
  try{return List.of(process(u,c,Profile.representation(raw)));}catch(Exception e){throw new InvalidAuthorizationDetailsException("Invalid stored grant");}
 }
 public void afterAuthorizationDetailsProcessed(UserSessionModel u,ClientSessionContext c,AuthorizationDetailsJSONRepresentation d){}
 public void close(){}
}
