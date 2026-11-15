FROM maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS build
WORKDIR /build
COPY extension/pom.xml .
COPY extension/src src
RUN mvn -B -q package
FROM quay.io/keycloak/keycloak:26.8.1@sha256:3f3c5f8e03c614774b4bd9173b88391fefa4153bfc010d8012d59ad825377332
COPY --from=build /build/target/rar-lab.jar /opt/keycloak/providers/rar-lab.jar
COPY themes/rar-lab /opt/keycloak/themes/rar-lab
