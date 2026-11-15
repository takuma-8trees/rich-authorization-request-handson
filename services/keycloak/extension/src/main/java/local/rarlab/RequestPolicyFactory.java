package local.rarlab;
import java.util.List;
import org.keycloak.Config;
import org.keycloak.models.*;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.services.clientpolicy.executor.*;
public final class RequestPolicyFactory implements ClientPolicyExecutorProviderFactory {
 public ClientPolicyExecutorProvider create(KeycloakSession s){return new RequestPolicy();}
 public String getId(){return "rar-lab-policy";} public String getHelpText(){return "Validate the closed document RAR profile.";}
 public void init(Config.Scope c){}public void postInit(KeycloakSessionFactory f){}public void close(){}
 public List<ProviderConfigProperty> getConfigProperties(){return List.of();}
}
