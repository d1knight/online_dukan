# 🛒 Online Dúkan API

Bul proekt **Python** hám **Django REST Framework** platformasında jaratılǵan, joqarı dárejeli hám qáwipsiz internet-dúkan API sisteması. Proekt quramına Telegram arqalı avtorizaciya, aqıllı sebet basqarıwı hám qáwipsizlik sistemaları kiredi.

---

## 🌟 Tiykarǵı múmkinshilikler

*   **🤖 Telegram Avtorizaciya:** Parolsiz avtorizaciya sisteması. Paydalanıwshı Telegram-bot arqalı bir mártelik 6 sanlı OTP-kod aladı hám sol arqalı sistemaǵa kiredi.
*   **📦 Skladtı basqarıw:** Buyırtpa beriw waqtında sistema avtomat túrde tawardıń qoymada bar-joqlıǵın tekseredi hám rezervke alıp, qaldıqtı (`stock`) kemeytedi.
*   **💳 Buyırtpa logikası:**
    *   Buyırtpa statusları: `pending` (kútilmekte) -> `paid` (tólendi) -> `shipped` (jiberildi) -> `canceled` (biykar etildi).
    *   Tólem procesiniń imitaciyası ushın bólek endpoint jaratılǵan.
    *   Tawar bahası satıp alınǵan waqıttaǵı baha boyınsha saqlanadı (bahalar ózgerse de, tariyx ózgermeydi).
*   **⭐ Aqıllı pikirler (Reviews):** Tawarǵa pikir qaldırıw yamasa baha beriw imkaniyatı tek tawar **satıp alınǵan hám tólengen** jaǵdayda ǵana ashıladı.
*   **🛡 Qáwipsizlik hám sheklewler:**
    *   **JWT (SimpleJWT):** Tokenler arqalı qáwipsiz baylanıs.
    *   **Throttling (Rate Limit):** OTP-kodlardı tańlawdan (brute-force) qorǵaw (5 ret/min) hám spamlardan qorǵanıw.
    *   **Permissions:** Admin, Klient hám Miyman rollerin anıq ajıratıw.
*   **🔍 Izlew hám filtrlew:** Tawarlardı atı boyınsha izlew, bahası (`min`/`max`) hám kategoriyalar boyınsha filtrlew.
*   **📄 Dokumentaciya:** Swagger/OpenAPI járdeminde barlıq endpointlerdiń tolıq túsindirmesi.

---

## 🛠 Texnologiyalar

- **Til:** Python 3.10+
- **Framework:** Django 4.2+, DRF 3.14+
- **Maǵlıwmatlar bazası:** PostgreSQL
- **Avtentifikaciya:** JWT (SimpleJWT) + Telegram Bot API
- **Dokumentaciya:** `drf-spectacular` (Swagger UI)
- **Qosımsha ásbaplar:** Docker, Docker-Compose, `django-filter`

---

## ⚙️ Iske túsiriw (Docker járdeminde)

1.  **Repozitoriydi júklep alıń:**
    ```bash
    git clone https://github.com/d1knight/online_dukan.git
    cd online_dukan
    ```

2.  **Sazlamalardı ornatıń:**
    Proekt papkasında `.env` faylın jaratıń hám tómendegi maǵlıwmatlardı kiritiń:
    ```ini
    DEBUG=True
    SECRET_KEY=sizdiń-jasırın-koduńız
    ALLOWED_HOSTS=localhost,127.0.0.1

    # Maǵlıwmatlar bazası
    DB_NAME=dukan_db
    DB_USER=postgres
    DB_PASSWORD=sizdiń_paroluńız
    DB_HOST=db
    DB_PORT=5432

    # Telegram Bot
    TELEGRAM_BOT_TOKEN=botfatherdan-alınǵan-token
    ```

3.  **Proektti iske túsiriń:**
    ```bash
    docker-compose up --build
    ```

4.  **Maǵlıwmatlar bazasın tayarlaw hám Admin (Superuser) jaratıw:**
    ```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser
    ```

---

## 📖 Tiykarǵı API Endpointler

### Avtorizaciya
*   `POST /api/auth/telegram/webhook/` — Telegram-dan maǵlıwmatlardı qabıllaw.
*   `POST /api/auth/telegram/` — OTP-kodtı JWT tokenge almastırıw.

### Dúkan funksiyaları
*   `GET /api/products/` — Tawarlar dizimi (Filtrler: `min_price`, `max_price`, `category`).
*   `POST /api/products/{id}/add_review/` — Pikir qaldırıw (tek tólemden soń).
*   `GET /api/cart/` — Sebetti kóriw (paginaciya hám ulıwma summa menen).
*   `POST /api/orders/checkout/` — Sebetten buyırtpa jaratıw.
*   `POST /api/orders/{id}/pay/` — Buyırtpa ushın tólem qılıw.

---

## 👤 Avtor

**Maman Dáwletov**
*   **GitHub:** [@d1knight](https://github.com/d1knight)
*   **Proekt maqseti:** Bul proekt joqarı dárejeli API proektlestiriw hám qáwipsiz internet-dúkan sistemasın jaratıw boyınsha úlgi retinde islep shıǵılǵan.

---

### 📝 Eskertpe
Bul sistema `drf-spectacular` járdeminde avtomat túrde hújjetlestirilgen. Iske túsirgenińizden soń, barlıq endpointler menen tómendegi mánzil boyınsha tanısıp shıǵıwıńız múmkin:
👉 **[http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)**