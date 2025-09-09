function el(id) { return document.getElementById(id) }

function readDbParams() {
  const dbChoice = document.querySelector('input[name="db-choice"]:checked').value;
  let db = {};

  if (dbChoice === 'custom') {
    const host = el('host').value.trim();
    const port = el('port').value.trim();
    const dbname = el('dbname').value.trim();
    const user = el('user').value.trim();
    const password = el('password').value.trim();

    if (host) db.host = host;
    if (port) db.port = port;
    if (dbname) db.dbname = dbname;
    if (user) db.user = user;
    if (password) db.password = password;
  }

  return Object.keys(db).length ? db : undefined;
}

function toggleDbParams() {
  const dbChoice = document.querySelector('input[name="db-choice"]:checked').value;
  const customDbParams = el('custom-db-params');
  
  if (dbChoice === 'custom') {
    customDbParams.style.display = 'block';  // Показываем поля для своей базы
  } else {
    customDbParams.style.display = 'none';   // Скрываем поля для своей базы
  }

  // Отправляем состояние dbChoice на сервер
  sendDbChoiceToServer(dbChoice);
}

// Функция для отправки состояния dbChoice на сервер
// Функция для отправки состояния dbChoice на сервер
// Функция для отправки состояния dbChoice на сервер
async function sendDbChoiceToServer(dbChoice) {
  try {
    const response = await fetch('/save_db_choice/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      // Отправляем строку напрямую, а не объект
      body: JSON.stringify({ db_choice: dbChoice })  
    });

    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        log('Состояние dbChoice успешно сохранено.');
      }
    } else {
      log('Ошибка при сохранении состояния dbChoice.');
    }
  } catch (e) {
    log('Ошибка при отправке состояния dbChoice: ' + e.message);
  }
}



// Логирование сообщений
function log(msg) {
  const box = el('log');
  const time = new Date().toLocaleTimeString();
  const div = document.createElement('div');
  div.className = 'small';
  div.textContent = `[${time}] ${msg}`;
  box.prepend(div);
}

function showResult(data) {
  const pre = el('result');
  try {
    pre.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    pre.textContent = String(data);
  }
}

// Отправка данных на сервер в формате JSON
async function postJson(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

// Обработчики для кнопок
async function handleRunExplain() {
  const query = el('query').value.trim();
  if (!query) { alert('Нужно ввести SQL запрос.'); return; }
  const body = { query, db_params: readDbParams() };
  log('Запрос: run_explain');
  showResult('Loading...');
  try {
    const json = await postJson('/run_explain/', body);
    showResult(json);
    log('run_explain успешно');
  } catch (e) {
    showResult({ error: e.message });
    log('Ошибка: ' + e.message);
  }
}

async function handleAnalyzeIndexes() {
  const query = el('query').value.trim();
  if (!query) { alert('Нужно ввести SQL запрос.'); return; }
  const body = { query, db_params: readDbParams() };
  log('Запрос: analyze_indexes');
  showResult('Loading...');
  try {
    const json = await postJson('/analyze_indexes/', body);
    showResult(json);
    log('analyze_indexes успешно');
  } catch (e) {
    showResult({ error: e.message });
    log('Ошибка: ' + e.message);
  }
}

async function handleAnalyzeStats() {
  const body = { db_params: readDbParams() };
  log('Запрос: analyze_stats');
  showResult('Loading...');
  try {
    const json = await postJson('/analyze_stats/', body);
    showResult(json);
    log('analyze_stats успешно');
  } catch (e) {
    showResult({ error: e.message });
    log('Ошибка: ' + e.message);
  }
}

async function handleGetRecs() {
  const body = { db_params: readDbParams() };
  log('Запрос: get_postgres_recommendations');
  showResult('Loading...');
  try {
    const json = await postJson('/get_postgres_recommendations/', body);
    showResult(json);
    log('get_postgres_recommendations успешно');
  } catch (e) {
    showResult({ error: e.message });
    log('Ошибка: ' + e.message);
  }
}

async function handleNPlus1() {
  const body = { db_params: readDbParams() };
  log('Запрос: analyze_n_plus_one');
  showResult('Loading...');
  try {
    const json = await postJson('/analyze_n_plus_one/', body);
    showResult(json);
    log('analyze_n_plus_one успешно');
  } catch (e) {
    showResult({ error: e.message });
    log('Ошибка: ' + e.message);
  }
}

function handleClear() {
  showResult('Ничего не запущено.');
}

// Инициализация
function init() {
  el('db-pagila').addEventListener('change', toggleDbParams);
  el('db-custom').addEventListener('change', toggleDbParams);

  // Инициализируем начальное состояние
  toggleDbParams();

  el('btn-run-explain').addEventListener('click', handleRunExplain);
  el('btn-analyze-indexes').addEventListener('click', handleAnalyzeIndexes);
  el('btn-analyze-stats').addEventListener('click', handleAnalyzeStats);
  el('btn-get-recs').addEventListener('click', handleGetRecs);
  el('btn-nplus1').addEventListener('click', handleNPlus1);
  el('btn-clear').addEventListener('click', handleClear);
  el('btn-save-db').addEventListener('click', async function () {
    const dbParams = readDbParams();

    if (!dbParams) {
      alert('Пожалуйста, заполните все параметры подключения.');
      return;
    }

    try {
      const response = await postJson('/save_db_params/', dbParams);  // Отправляем как JSON
      if (response.success) {
        log('Параметры базы данных успешно сохранены.');
        console.log('Сохраненные параметры:', response.saved_db_params);
        // Отобразить параметры в журнале
        log('Сохраненные параметры базы данных:');
        log(JSON.stringify(response.saved_db_params, null, 2));
      } else {
        log('Ошибка при сохранении параметров базы данных.');
      }
    } catch (error) {
      log('Ошибка: ' + error.message);
    }
  });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
