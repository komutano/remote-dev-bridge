# RemoteDevBridge (remote-dev-bridge)

> **Masaüstünüzdeki AI kodlama ajanlarını ve yerel projelerinizi Telegram üzerinden cep telefonunuza bağlayan açık kaynaklı köprü.**  
> Sıfır kişisel veri sızıntısı ve Sıfır Güven (Zero-Trust) mimarisiyle dilediğiniz yerden kod yazdırın, diff inceleyin, dal açın ve GitHub'a push edin.

---

## 🌟 Vizyon: Tüm AI Katmanlarını Tek Bir Köprüde Birleştirmek

Geliştiriciler çoğu zaman masalarının başında değilken akıllarına parlak bir fikir gelir veya acil bir hata düzeltilmesi gerekir. **RemoteDevBridge**, cep telefonunuzu bilgisayarınız için güvenli bir uzaktan kumandaya dönüştürür.

Farklı araçlar arasında bölünmek yerine, **tüm bu katmanları tek bir programda birleştirirsiniz**:

```
                       📱 Cep Telefonunuz (Telegram)
                                     │
                       🔐 Sıfır Güven & Git Koruması
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌──────────────────────┐                           ┌──────────────────────┐
│   AI Motor Katmanı   │                           │  Çalışma & Git Katmanı│
├──────────────────────┤                           ├──────────────────────┤
│ 1. Google AI Studio  │ (Doğrudan API, CLI gerekmez)│ • /status & /diff  │
│ 2. Claude Code CLI   │ (claude -p)               │ • /do (otomatik dal) │
│ 3. Gemini CLI        │ (Resmi Google CLI)        │ • /push (commit & PR)│
│ 4. OpenCode & NVIDIA │ (NVIDIA NIM, Ollama)      │ • /ls & /file okuma  │
│ 5. Özel CLI / Aider  │ (İsteğe bağlı şablonlar)  │ • /open (IDE açma)   │
└──────────────────────┘                           └──────────────────────┘
```

Bilgisayarınızda VS Code veya Antigravity'nin açık olmasına gerek yoktur. AI motorları masaüstünüz kilitli olsa dahi arka planda sessizce çalışır. Masanıza geçmeden önce tek bir `/open` komutu vererek projenin istediğiniz IDE'de ekrana gelmesini sağlayabilirsiniz.

---

## 🚀 Öne Çıkan Yetenekler

### 1. Evrensel AI Motor Desteği
- **Doğrudan Google AI Studio (`AI_ENGINE=gemini-direct`):** Bilgisayarınıza hiçbir harici npm/pip CLI paketi kurmadan, yalnızca Google AI Studio'dan aldığınız ücretsiz API anahtarıyla çalışır. Gemini'nin devasa 1 Milyon+ token penceresiyle tüm projeyi tek seferde analiz eder.
- **Resmi Gemini CLI (`AI_ENGINE=gemini`):** Google'ın terminal tabanlı resmi CLI aracını çalıştırır.
- **Claude Code CLI (`AI_ENGINE=claude`):** Anthropic'in otonom kodlama ajanını non-interactive parametrelerle çalıştırır.
- **OpenCode & NVIDIA NIM (`AI_ENGINE=opencode`):** OpenAI-uyumlu standart sayesinde **NVIDIA NIM** (Llama 3.3 70B, DeepSeek R1/V3), Groq veya yerel Ollama modellerini bağlayarak çalıştırır.
- **Özel Komut Şablonları (`AI_ENGINE=custom`):** Aider veya kendi geliştirdiğiniz özel betikleri bağlayabilirsiniz.

### 2. Mobilden Eksiksiz Git Döngüsü
- **/do `<proje> <talimat>`:** Ana dalınızı korumak için otomatik olarak `mobile/YYYYMMDD-HHMMSS` formatında izole bir Git dalı açar, talimatı çalıştırır ve etkilenen dosyaların özetini döner.
- **/status `<proje>`:** Anlık `git status -sb` çıktısı sunar.
- **/diff `<proje>`:** Yapılan satır satır kod değişikliklerini Telegram sohbetinde görüntüler.
- **/push `<proje> [mesaj]`:** Değişiklikleri sahneler (`git add -A`), commit atar ve dalı doğrudan uzak depoya (`origin`) push'lar. Telefonunuzdaki GitHub uygulamasından tek tıkla Pull Request (PR) açabilirsiniz.

### 3. Dosya Gezgini ve Masaüstü Başlatıcı
- **/ls `<proje> [alt_klasor]`:** Güvenli şekilde klasörleri listeler; `.git`, `node_modules` ve gereksiz önbellek klasörlerini otomatik gizler.
- **/file `<proje> <dosya_yolu>`:** Kod dosyalarını mesaj içinde okumanızı sağlar; büyük dosyaları doğrudan Telegram belgesi olarak telefona indirir.
- **/open `<proje> [dosya_yolu]`:** Bilgisayarınızdaki editörü (Antigravity, VS Code, Cursor) tetikleyerek projeyi masaüstünüzde açar.

---

## 🛡️ Güvenlik ve Sıfır Kişisel Veri İlkesi

Bu proje, açık kaynak (public) olarak yayınlanmak üzere sıfır kişisel veri kuralıyla tasarlanmıştır:

1. **Katı Kullanıcı İzin Kilidi:** Yalnızca `.env` dosyasındaki `ALLOWED_USER_IDS` listesinde tanımlı Telegram kullanıcı ID'lerinden gelen istekler işlenir. Yetkisiz mesajlar sessizce reddedilir. Liste boşsa bot güvenlik gereği başlamaz.
2. **Dizin Aşımı Koruması (Path Traversal Guard):** `/ls`, `/file` veya `/open` ile istenen tüm yollar mutlak adrese dönüştürülür ve proje kök dizini sınırları dışına çıkılması engellenir.
3. **Kirli Çalışma Ağacı Koruması (Dirty Working Tree):** `/do` komutu çalışmadan önce bilgisayarınızda yarım kalmış uncommitted değişiklik olup olmadığını kontrol eder. Yerel emeğinizi kaybetmemeniz için işlem durdurulur.
4. **Eşzamanlılık Kilidi (`ProjectLock`):** Proje bazlı kilit mekanizması sayesinde aynı anda gelen çakışan komutların dosyaları bozması önlenir.
5. **Windows 11 ve UTF-8 Desteği:** Türkçe karakter sorunlarını önlemek için `PYTHONIOENCODING=utf-8` zorlanır ve zaman aşımında yetim süreçler (`taskkill`) temizlenir.

---

## ⚡ 2 Dakikada Hızlı Kurulum

### 1. Depoyu Klonlayın ve Bağımlılıkları Yükleyin
```bash
git clone https://github.com/kullanici-adiniz/remote-dev-bridge.git
cd remote-dev-bridge

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 📱 Adım Adım Telegram Botu ve Kimlik Kurulumu

Bu köprüyü kullanabilmek için kendinize ait bir Telegram botuna ve değişmeyen sayısal Telegram kimlik numaranıza ihtiyacınız vardır.

### A. Botu Oluşturma ve Token Alma (BotFather)
1. Telegram arama çubuğuna **`@BotFather`** yazın (resmi onaylı hesap).
2. Sohbeti başlatıp **`/newbot`** komutunu gönderin.
3. Botunuza bir **Görünen Ad** verin (Örn: `Murat Dev Bridge`).
4. Botunuza sonu mutlaka `bot` veya `_bot` ile biten benzersiz bir **Kullanıcı Adı (Username)** verin (Örn: `murat_devbridge_bot`).
5. BotFather size kırmızı renkle vurgulanan bir **API Token** verecektir (`7891234567:AAFl...`). Bu token'ı `.env` dosyanızdaki `TELEGRAM_BOT_TOKEN` kısmına yapıştırın.

### B. Sayısal Telegram Kullanıcı Kimliğinizi (User ID) Öğrenme
Telegram'da kullanıcı adınızı değiştirseniz bile **User ID numaranız asla değişmez**. Bot, yabancıların bilgisayarınıza erişmesini engellemek için sizi bu değişmeyen numarayla tanır:
1. Telegram'da **`@userinfobot`** veya **`@raw_data_bot`** botunu aratıp başlatın.
2. Botun size gönderdiği karttaki `Id: 123456789` sayısını kopyalayın.
3. Bu sayıyı `.env` dosyasındaki `ALLOWED_USER_IDS` kısmına yazın (`ALLOWED_USER_IDS=123456789`).

> [!IMPORTANT]
> **Sıfır Güvenlik Açığı (Zero-Trust):** Eğer `ALLOWED_USER_IDS` boş bırakılırsa bot güvenlik gereği hiç başlamaz. Tanımlı olmayan yabancı biri botunuzu bulup mesaj atsa bile bot hiçbir yanıt vermez ve isteği terminale güvenlik uyarısı düşerek sessizce engeller.

### C. Ekstra Telegram Gizlilik Ayarı (Önerilen)
Yabancı kişilerin botunuzu rastgele Telegram gruplarına eklemesini engellemek için:
- `@BotFather` içinde `/setjoingroups` yazın, botunuzu seçin ve **`Disable`** yapın.

---

### 2. Ayar Dosyasını Oluşturun (`.env`)
`.env.example` dosyasını `.env` olarak kopyalayın:
```bash
cp .env.example .env
```
`.env` dosyanızı açıp bilgilerinizi girin:
```env
TELEGRAM_BOT_TOKEN=7891234567:AAFlKj9_xYzAbCdEfGhIjKlMnOpQrStUvWx
ALLOWED_USER_IDS=123456789

# Kullanmak istediğiniz AI motoru:
# 'gemini-direct' -> Google AI Studio anahtarınızla ek CLI kurmadan doğrudan çalışır
AI_ENGINE=gemini-direct
GEMINI_API_KEY=AIzaSySizinGoogleAIStudioAnahtariniz

# Masaüstü IDE başlatıcı ('code', 'agy', 'cursor'):
IDE_COMMAND=code
```

### 3. Projelerinizi Tanımlayın (`projects.json`)
`projects.example.json` dosyasını `projects.json` olarak kopyalayın:
```bash
cp projects.example.json projects.json
```
Yönetmek istediğiniz yerel projelerinizi eşleyin:
```json
{
  "web-sitem": {
    "path": "C:/Projelerim/web-sitem",
    "description": "Frontend Uygulamam"
  },
  "api": {
    "path": "C:/Projelerim/backend-api",
    "description": "FastAPI Servisi"
  }
}
```

### 4. Botu Başlatın

#### Windows Kullanıcıları İçin (Tek Tıkla):
Klasördeki **`start_bot.bat`** dosyasına çift tıklayarak botu doğrudan başlatabilirsiniz!

#### Komut Satırından:
```bash
python main.py
```

> [!IMPORTANT]
> **Pencerenin Açık Kalması Hakkında:**  
> RemoteDevBridge, komutları doğrudan kendi yerel bilgisayarınızda çalıştıran bir köprüdür. Bu nedenle **açılan terminal penceresinin ve bilgisayarınızın açık kalması gerekir.**  
> - **Ekranı Kilitleyebilirsiniz:** Masanızdan kalkarken ekranınızı kilitleyebilirsiniz (`Win + L`); ekran kilitli olsa dahi bot arka planda çalışmaya ve telefonunuzdan gelen talimatları yerine getirmeye devam eder.  
> - **Simge Durumuna Küçültebilirsiniz:** Konsol penceresini görev çubuğuna küçültebilirsiniz.  
> - **Pencere Kapanırsa:** Terminal penceresini tamamen kapatırsanız veya bilgisayar uyku/kapanma moduna geçerse bot uykuya dalar ve mesajlara yanıt veremez (ancak botu tekrar açtığınız anda birikmiş mesajlar sırayla işlenir).

---

## 📲 Telefondan Hızlı Kullanım ve `[Menü]` Butonu

Telefonda komutları tek tek elle yazmakla uğraşmamanız için RemoteDevBridge, açıldığı anda tüm komutları Telegram sunucularına otomatik olarak kaydeder (`set_my_commands`).

- **Menü Butonu:** Telegram'da botunuzun sohbet ekranını açtığınızda mesaj çubuğunun sol altında mavi bir **`[Menü]`** butonu belirir.
- **Otomatik Tamamlama:** Butona bastığınızda veya klavyeden sadece tek bir **`/`** yazdığınızda tüm komutlar açıklamalarıyla birlikte listelenir; tek tıkla seçip parametrenizi ekleyebilirsiniz.
- **Menü Hemen Görünmezse:** Telegram mobil uygulaması arayüzü önbelleğe alabilir. Menünün belirmesi için sohbet çubuğuna bir kez `/` yazmanız veya Telegram uygulamasını kapatıp tekrar açmanız yeterlidir.

Dilerseniz `@BotFather` üzerinden `/setcommands` komutunu kullanarak şu hazır listeyi yapıştırıp menüyü kalıcı da kılabilirsiniz:
```text
start - Bot durumu ve yardım menüsü
projects - Tanımlı projeleri listele
status - <proje> Git dalı ve temizlik durumu
diff - <proje> Yapılan değişiklikleri göster
push - <proje> [mesaj] Değişiklikleri commit ve push et
ask - <proje> <soru> Salt okunur kod analizi
do - <proje> <talimat> Dal açarak AI ile kod yazdır
ls - <proje> [klasör] Dosya ve klasörleri listele
file - <proje> <yol> Dosya içeriğini oku veya indir
open - <proje> [yol] Masaüstü IDE ile projeyi aç
```

---

## 📋 Telegram Komut Rehberi

| Komut | Açıklama |
| :--- | :--- |
| `/start` | Bot durumu, aktif motor ve yardım menüsü |
| `/engine [ad]` | **AI Motoru Seçimi:** Butonlara dokunarak veya yazarak motor değiştirme (`nvidia`, `gemini-direct`) |
| `/ai <soru>` | **Genel AI Danışmanı:** Projesiz serbest soru sorma (algoritmalar, mimari, hata çözümü, kodlama) |
| `/projects` | Tanımlı projelerin takma adları ve dizin durumları |
| `/status <proje>` | Git dal adı ve çalışma ağacı durumunu gösterir |
| `/diff <proje>` | Yapılan değişikliklerin satır satır farklarını (`git diff`) döner |
| `/push <proje> [mesaj]` | Değişiklikleri sahneler, commit atar ve remote'a push eder |
| `/ask [proje] <soru>` | Kod tabanını analiz eder (proje yazılmazsa otomatik genel soruya geçer) |
| `/do <proje> <talimat>` | Güvenli yeni dal açarak AI'a kod yazdırır |
| `/ls <proje> [klasor]` | Proje içi dosya ve klasörleri güvenle listeler |
| `/file <proje> <yol>` | Dosya içeriğini okur veya belge olarak telefona indirir |
| `/open <proje> [yol]` | Bilgisayarınızda projeyi veya dosyayı IDE ile açar |

---

## 🗺️ Gelecek Yol Haritası (Roadmap)

RemoteDevBridge, mobil uzaktan kodlama ve otonom yazılım geliştirme deneyimini en üst seviyeye taşımak için sürekli gelişmektedir:

- [x] **v1.0 (Mevcut Sürüm - Yayında):**
  - ✅ Google AI Studio (Gemini) ve NVIDIA NIM (Nemotron) doğrudan çift motor desteği.
  - ✅ Telegram üzerinden tek dokunuşla interaktif motor değiştirici (`/engine`).
  - ✅ Sıfır Güven (Zero-Trust) yetkilendirme, Git Dirty Tree koruması ve Path Traversal önleme.
  - ✅ Mobilden tam Git döngüsü (`/do`, `/status`, `/diff`, `/push`).
  - ✅ Dosya gezgini (`/ls`, `/file`) ve masaüstü IDE başlatıcı (`/open`).
  - ✅ Projesiz serbest teknik ve yazılım danışmanı (`/ai` - mimari, algoritmalar, kod).

- [ ] **v1.5 (Yakında - Geliştirme Aşamasında):**
  - 🔄 **İnteraktif Terminal Köprüsü (Human-in-the-Loop PTY):** Claude Code veya CLI ajanları çalışırken durup onay istediğinde (*"Değişikliği onaylıyor musunuz? (Y/n)"*), sorunun Telegram'a butonlarla (`[ ✅ Onayla ]` / `[ ❌ Reddet ]`) gelmesi ve verilen yanıtın gerçek zamanlı olarak bilgisayardaki terminale aktarılması.
  - 🔄 **Çoklu Kanal Desteği:** Discord Botu ve Slack webhook adaptörleri.

- [ ] **v2.0 (Planlanan Gelecek Hedefleri):**
  - 🚀 **Doğrudan Antigravity IDE Entegrasyonu (MCP Server):** Antigravity için yerel MCP (Model Context Protocol) sunucusu. Masanızdan kalktığınızda Antigravity'deki uzun süren görevlerin ilerleme durumunun ve onay isteklerinin doğrudan Telegram'a anlık bildirim olarak akması.
  - 🎙️ **Sesli Kodlama (Voice-to-Code):** Telegram'dan atılan sesli mesajların otomatik olarak çözümlenip kodlama talimatına dönüştürülmesi.

---

## 🙏 Geliştirici Teşekkürü

Açık kaynak dünyasında üretken yapay zekayı ve otonom yazılım geliştirmeyi ileriye taşıyan iki büyük teknoloji ekibine içtenlikle teşekkür ederiz:

- **Google AI Studio Ekibi:** Bağımsız geliştiricilere sundukları ultra hızlı Gemini modelleri, benzersiz bağlam pencereleri ve cömert ücretsiz kota ile bu tür uzaktan köprülerin her yazılımcı tarafından maliyetsiz kullanılabilmesini mümkün kıldıkları için.
- **NVIDIA:** Geliştiricilere yönelik **NVIDIA NIM** platformuyla açık ağırlıklı modellerin (Llama 3.3, DeepSeek, Mistral) yüksek performansla çalışmasını sağlayıp standart API'lerle bağımsız geliştiricilerin gücüne güç kattıkları için.

---

## 📄 Lisans

Bu proje özgür ve esnek [MIT Lisansı](LICENSE) altında sunulmaktadır.
