const axios = require('axios');

const BASE_URL = 'http://localhost:5001';
const LOGIN_URL = `${BASE_URL}/login`;
const VERIFY_OTP_URL = `${BASE_URL}/verify-otp`;
const SIGNUP_URL = `${BASE_URL}/signup`;
const LIKE_PRODUCT_URL = `${BASE_URL}/likeProduct`;

// Funzione helper per misurare tempo
async function runWithTiming(label, fn) {
  const start = Date.now();
  await fn();
  const end = Date.now();
  console.log(`${label} completato in ${end - start} ms\n`);
}

//LOGIN 
async function testLoginUserRole() {
  console.log("Login utente ruolo 'user' (JWT)");
  await post(LOGIN_URL, {
    email: 'user1@gmail.com',
    password: 'user1'
  });
}

async function testLoginAdminRole() {
  console.log("Login utente admin (OTP)");
  await post(LOGIN_URL, {
    email: 'user2@gmail.com',
    password: 'user2'
  });
}

async function testLoginInvalidPassword() {
  console.log("Login con password errata");
  await post(LOGIN_URL, {
    email: 'user2@gmail.com',
    password: 'sbagliata'
  });
}

async function testLoginNonexistentUser() {
  console.log("Login con email inesistente");
  await post(LOGIN_URL, {
    email: 'inesistente@gmail.com',
    password: 'user2'
  });
}

//OTP 
async function testVerifyOtpValid() {
  console.log("OTP valido");
  await post(VERIFY_OTP_URL, {
    email: 'user3@gmail.com',
    otp: '905569'
  });
}

async function testVerifyOtpMissingFields() {
  console.log("OTP mancante");
  await post(VERIFY_OTP_URL, {
    email: 'user2@gmail.com'
  });
}

async function testVerifyOtpWrongCode() {
  console.log("OTP errato");
  await post(VERIFY_OTP_URL, {
    email: 'user1@example.com',
    otp: '000000'
  });
}

async function testVerifyOtpUnknownEmail() {
  console.log("Email non esistente (OTP)");
  await post(VERIFY_OTP_URL, {
    email: 'inesistente@example.com',
    otp: '123456'
  });
}

//SIGNUP
async function testSignupUser() {
  console.log("Signup utente normale (user)");
  await post(SIGNUP_URL, {
    email: 'user121@gmail.com',
    manufacturer: 'user121',
    password: 'user12'
  });
}

async function testSignupExistingEmail() {
  console.log("Signup con email già registrata");
  await post(SIGNUP_URL, {
    email: 'user121@gmail.com',
    manufacturer: 'user121',
    password: 'user12'
  });
}

async function testSignupProducerWithToken() {
  console.log("Signup producer con token");
  await post(SIGNUP_URL, {
    email: 'producer171@example.com',
    manufacturer: 'user171',
    password: 'PSW',
    role: 'producer',
    inviteToken: 'ABC123'
  });
}

async function testSignupProducerWithoutToken() {
  console.log("Signup producer senza token");
  await post(SIGNUP_URL, {
    email: 'producer239@example.com',
    manufacturer: 'user239',
    password: 'PSW',
    role: 'producer'
  });
}

//LIKE PRODUCT TEST 
async function testLikeProduct() {
    console.log("Like product");
  
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTM4Njg5MSwianRpIjoiNzA1MzJmZTgtZGZiMC00MWExLWIyMDYtMTYyYWU1ODk1ZDg4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InVzZXIxQGdtYWlsLmNvbSIsIm5iZiI6MTc1MTM4Njg5MSwiY3NyZiI6ImYxMTk5YzFiLWZjNmQtNDBlZi1iYWNhLWZjNjA0OWNkNzIyZiIsImV4cCI6MTc1MTM4Nzc5MX0.8-gvprXK5I8mKnuDxEoi3I1cdDV7MVysc5X-aD2e1xM'; 
  
    const product = {
      ID: '67891',
      Name: 'pera',
      Manufacturer: 'user90'
    };
  
    try {
      const response = await axios.post(
        LIKE_PRODUCT_URL,
        { product },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
  
      console.log('Status:', response.status);
      console.log('Response:', response.data, '\n');
    } catch (error) {
      const res = error.response;
      console.error('Errore Like Product:', res?.status, res?.data || error.message, '\n');
    }
  }
  
  //UNLIKE PRODUCT TEST
async function testUnlikeProduct() {
    console.log("Unlike product");
  
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MTM4Njg5MSwianRpIjoiNzA1MzJmZTgtZGZiMC00MWExLWIyMDYtMTYyYWU1ODk1ZDg4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InVzZXIxQGdtYWlsLmNvbSIsIm5iZiI6MTc1MTM4Njg5MSwiY3NyZiI6ImYxMTk5YzFiLWZjNmQtNDBlZi1iYWNhLWZjNjA0OWNkNzIyZiIsImV4cCI6MTc1MTM4Nzc5MX0.8-gvprXK5I8mKnuDxEoi3I1cdDV7MVysc5X-aD2e1xM';
  
    const productId = '67891'; // deve corrispondere a quello del like
  
    try {
      const response = await axios.delete(`${BASE_URL}/unlikeProduct`, {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: {
          productId: productId
        }
      });
  
      console.log('Status:', response.status);
      console.log('Response:', response.data, '\n');
    } catch (error) {
      const res = error.response;
      console.error('Errore Unlike Product:', res?.status, res?.data || error.message, '\n');
    }
  }
  
  //ADD RECENTLY SEARCHED
async function testAddRecentlySearched() {
    console.log("Add recently searched");
  
    const payload = {
      userEmail: 'user1@gmail.com', 
      product: {
        ID: '55555',
        Name: 'Mela',
        Manufacturer: 'user345',
        CreationDate: '2025-10-01'
      }
    };
  
    try {
      const response = await axios.post(`${BASE_URL}/addRecentlySearched`, payload);
      console.log('Status:', response.status);
      console.log('Response:', response.data, '\n');
    } catch (error) {
      const res = error.response;
      console.error('Errore addRecentlySearched:', res?.status, res?.data || error.message, '\n');
    }
  }
  


async function post(url, payload) {
  try {
    const { data, status } = await axios.post(url, payload);
    console.log('Status:', status);
    console.log('Response:', data, '\n');
  } catch (err) {
    const res = err.response;
    console.error('Error:', res?.status, res?.data || err.message, '\n');
  }
}


async function runAllTests() {
  console.log('ESECUZIONE COMPLETA\n');
  const startAll = Date.now();

  await runWithTiming("Login utente ruolo 'user'", testLoginUserRole);
  await runWithTiming("Login utente admin", testLoginAdminRole);
  await runWithTiming("Login con password errata", testLoginInvalidPassword);
  await runWithTiming("Login con email inesistente", testLoginNonexistentUser);

  await runWithTiming("OTP valido", testVerifyOtpValid);
  await runWithTiming("OTP mancante", testVerifyOtpMissingFields);
  await runWithTiming("OTP errato", testVerifyOtpWrongCode);
  await runWithTiming("OTP email non esistente", testVerifyOtpUnknownEmail);

  await runWithTiming("Signup utente normale", testSignupUser);
  await runWithTiming("Signup email già esistente", testSignupExistingEmail);
  await runWithTiming("Signup producer con token", testSignupProducerWithToken);
  await runWithTiming("Signup producer senza token", testSignupProducerWithoutToken);

  await runWithTiming("Like prodotto", testLikeProduct);
  await runWithTiming("Unlike prodotto", testUnlikeProduct);

  await runWithTiming("Add recently searched", testAddRecentlySearched);



  const endAll = Date.now();
  console.log(`Tutti i test completati in ${(endAll - startAll) / 1000}s`);
}


if (require.main === module) {
  runAllTests();
}
