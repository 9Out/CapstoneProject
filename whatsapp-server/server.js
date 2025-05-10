const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const bodyParser = require('body-parser');
const cors = require('cors');

// Inisialisasi aplikasi Express
const app = express();
app.use(cors());
app.use(bodyParser.json());

// Inisialisasi klien WhatsApp
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        headless: true,
    },
});

// Event: QR Code untuk autentikasi
client.on('qr', (qr) => {
    console.log('Silakan scan QR code berikut:');
    qrcode.generate(qr, { small: true });
});

// Event: Klien siap digunakan
client.on('ready', () => {
    console.log('Client WhatsApp siap!');
});

// Event: Jika autentikasi gagal
client.on('auth_failure', (msg) => {
    console.error('Autentikasi WhatsApp gagal:', msg);
});

// Event: Jika terputus, coba reconnect
client.on('disconnected', (reason) => {
    console.log('Client terputus:', reason);
    client.initialize();
});

// Event: Error
client.on('error', (error) => {
    console.error('Error terjadi:', error);
});

// Jalankan klien
client.initialize();

// Endpoint API untuk mengirim pesan WhatsApp
app.post('/send-message', async (req, res) => {
    try {
        const { phone, message } = req.body;

        if (!phone || !message) {
            return res.status(400).json({ success: false, error: 'Nomor HP dan pesan diperlukan' });
        }


        if (!client.info) {
            return res.status(503).json({ success: false, error: 'Client WhatsApp belum siap' });
        }

        const formattedPhone = `${phone.replace('+', '')}@c.us`;
        const response = await client.sendMessage(formattedPhone, message);

        return res.json({ success: true, data: response });
    } catch (error) {
        console.error('Gagal mengirim pesan:', error);
        return res.status(500).json({ success: false, error: error.message });
    }
});

// Endpoint untuk mengecek status server
app.get('/status', (req, res) => {
    return res.json({
        status: 'aktif',
        whatsappConnected: client.info ? true : false,
        timestamp: new Date()
    });
});

// Jalankan server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT}`);
});