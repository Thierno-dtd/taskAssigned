# Application Mobile Android - SEEG Intervention

Guide de développement et build pour l'application mobile Android.

## Architecture

L'application mobile communique avec l'API Django via:
- **Authentification**: JWT tokens + OTP SMS
- **Données**: API REST JSON
- **Localisation**: GPS natif Android
- **Stockage**: SQLite local + synchronisation cloud

## Prérequis

- Android Studio Hedgehog (2023.1.1) ou supérieur
- JDK 17+
- Android SDK API 26+ (Android 8.0+)
- Gradle 8.0+

## Structure du projet

```
mobile/android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/seeg/intervention/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── api/
│   │   │   │   │   ├── ApiService.kt
│   │   │   │   │   ├── AuthInterceptor.kt
│   │   │   │   │   └── RetrofitClient.kt
│   │   │   │   ├── ui/
│   │   │   │   │   ├── tasks/
│   │   │   │   │   ├── reports/
│   │   │   │   │   └── map/
│   │   │   │   ├── data/
│   │   │   │   │   ├── local/
│   │   │   │   │   └── remote/
│   │   │   │   └── utils/
│   │   │   ├── res/
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle.kts
├── gradle/
└── build.gradle.kts
```

## Configuration

### 1. Configurer l'URL de l'API

Dans `app/src/main/java/com/seeg/intervention/api/RetrofitClient.kt`:

```kotlin
object RetrofitClient {
    // Development
    // private const val BASE_URL = "http://10.0.2.2:8000/api/"
    
    // Production
    private const val BASE_URL = "https://api.seeg.ga/api/"
    
    // ...
}
```

### 2. Configuration des permissions

Dans `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.CAMERA" />
```

### 3. Configuration Google Maps (optionnel)

Si vous utilisez Google Maps, ajoutez votre clé API dans `AndroidManifest.xml`:

```xml
<meta-data
    android:name="com.google.android.geo.API_KEY"
    android:value="VOTRE_CLE_API_GOOGLE_MAPS" />
```

## Dépendances principales (build.gradle.kts)

```kotlin
dependencies {
    // Android Core
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    
    // Navigation
    implementation("androidx.navigation:navigation-fragment-ktx:2.7.6")
    implementation("androidx.navigation:navigation-ui-ktx:2.7.6")
    
    // ViewModel & LiveData
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0")
    
    // Retrofit (API REST)
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Room (Base de données locale)
    implementation("androidx.room:room-runtime:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    
    // Glide (Images)
    implementation("com.github.bumptech.glide:glide:4.16.0")
    kapt("com.github.bumptech.glide:compiler:4.16.0")
    
    // Google Maps
    implementation("com.google.android.gms:play-services-maps:18.2.0")
    implementation("com.google.android.gms:play-services-location:21.0.1")
    
    // QR Code Scanner
    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
    
    // Tests
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
```

## Build

### Build de développement

```bash
# Debug APK
./gradlew assembleDebug

# L'APK se trouve dans:
# app/build/outputs/apk/debug/app-debug.apk
```

### Build de production

```bash
# Générer le keystore (une seule fois)
keytool -genkey -v -keystore seeg-intervention.keystore -alias seeg \
  -keyalg RSA -keysize 2048 -validity 10000

# Build release
./gradlew assembleRelease

# L'APK signé se trouve dans:
# app/build/outputs/apk/release/app-release.apk
```

### Bundle pour Google Play

```bash
./gradlew bundleRelease

# Le bundle se trouve dans:
# app/build/outputs/bundle/release/app-release.aab
```

## Installation

### Sur émulateur

```bash
# Installer l'APK sur l'émulateur
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Sur appareil physique

1. Activer le mode développeur sur l'appareil
2. Activer le débogage USB
3. Connecter l'appareil via USB
4. Autoriser le débogage sur l'appareil

```bash
# Vérifier la connexion
adb devices

# Installer l'APK
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Fonctionnalités principales

### 1. Authentification
- Login avec username/password
- Login avec OTP SMS
- Stockage sécurisé du token JWT
- Rafraîchissement automatique du token

### 2. Gestion des tâches
- Liste des tâches assignées
- Détails de la tâche
- Marquer comme "en cours" / "terminée"
- Ajouter des notes
- Prendre des photos

### 3. Soumission de rapports
- Formulaire de rapport de fin
- Géolocalisation automatique
- Signature numérique
- Photos des travaux
- Rapport de non-exécution

### 4. Carte GPS
- Affichage des tâches sur la carte
- Navigation vers la tâche
- Filtrage par distance
- Vue satellite / plan

### 5. Mode hors-ligne
- Synchronisation des tâches
- Mise en cache des données
- Envoi des rapports en différé
- Indicateur de connexion

## API Endpoints utilisés

### Authentification
- `POST /api/auth/login/` - Login JWT
- `POST /api/auth/otp/request/` - Demander OTP
- `POST /api/auth/otp/verify/` - Vérifier OTP
- `POST /api/token/refresh/` - Rafraîchir token

### Tâches
- `GET /api/tasks/mes-taches/` - Liste des tâches
- `GET /api/tasks/taches/{id}/` - Détail tâche
- `PATCH /api/tasks/taches/{id}/` - Mettre à jour
- `POST /api/tasks/taches/{id}/sous-taches/` - Créer sous-tâche

### Rapports
- `POST /api/reports/rapports/` - Soumettre rapport
- `GET /api/reports/mes-rapports/` - Liste des rapports

### GPS
- `POST /api/tasks/taches/{id}/localisation/` - Mettre à jour position
- `GET /api/tasks/map/taches/` - Tâches pour la carte

## Troubleshooting

### Problème: Connexion refusée à l'API
- Vérifier que l'URL de l'API est correcte
- Vérifier que CORS est configuré sur le serveur
- Pour l'émulateur, utiliser `10.0.2.2` au lieu de `localhost`

### Problème: Permission GPS refusée
- Vérifier que les permissions sont déclarées dans AndroidManifest.xml
- Demander la permission à l'exécution (Android 6.0+)

### Problème: Photos non sauvegardées
- Vérifier les permissions de stockage
- Vérifier que le dossier media existe sur le serveur

## Ressources

- Documentation API: https://api.seeg.ga/api/docs/
- Repository: https://github.com/seeg/intervention-mobile
- Support: support@seeg.ga
