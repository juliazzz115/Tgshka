/*
  Настройка облачных аккаунтов (Apple ID, Google, вход по ссылке на почту)
  и хранения данных пользователей в облаке.

  Пока здесь null — приложение работает в локальном режиме
  (аккаунты и данные хранятся только на устройстве пользователя).

  Как включить облако (бесплатно, ~15 минут):
  1. Зайдите на https://console.firebase.google.com и создайте проект.
  2. Add app → Web (</>) — скопируйте объект firebaseConfig сюда вместо null.
  3. Authentication → Sign-in method → включите:
     - Google
     - Email link (passwordless sign-in)
     - Apple (нужен аккаунт Apple Developer, 99 $/год — требование Apple)
  4. Authentication → Settings → Authorized domains → добавьте домен,
     где размещено приложение (например, ваш-логин.github.io).
  5. Firestore Database → Create database → production mode, затем в Rules:

     rules_version = '2';
     service cloud.firestore {
       match /databases/{database}/documents {
         match /users/{uid} {
           allow read, write: if request.auth != null && request.auth.uid == uid;
         }
       }
     }

  Пример заполнения:
  window.FIREBASE_CONFIG = {
    apiKey: "AIza...",
    authDomain: "myapp.firebaseapp.com",
    projectId: "myapp",
    storageBucket: "myapp.appspot.com",
    messagingSenderId: "1234567890",
    appId: "1:1234567890:web:abc123"
  };
*/
window.FIREBASE_CONFIG = null;
