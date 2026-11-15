package local.rarlab;
import java.util.List;
import org.keycloak.Config;
import org.keycloak.authentication.*;
import org.keycloak.models.*;
import org.keycloak.provider.ProviderConfigProperty;
public final class ConsentFactory implements AuthenticatorFactory {
 public String getId(){return "rar-lab-consent";}public Authenticator create(KeycloakSession s){return new Consent();}
 public String getDisplayType(){return "RAR Lab consent";}public String getReferenceCategory(){return "consent";}
 public boolean isConfigurable(){return false;}public boolean isUserSetupAllowed(){return false;}
 public AuthenticationExecutionModel.Requirement[] getRequirementChoices(){return new AuthenticationExecutionModel.Requirement[]{AuthenticationExecutionModel.Requirement.REQUIRED};}
 public String getHelpText(){return "Confirm exact authorization details before issuing a token.";}
 public List<ProviderConfigProperty> getConfigProperties(){return List.of();}
 public void init(Config.Scope c){}public void postInit(KeycloakSessionFactory f){}public void close(){}
}
