const express = require('express');
const path = require('path');
const { generateAuthTicket, redeemAuthTicket } = require('./refresh');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/refresh', async (req, res) => {
    const roblosecurityCookie = req.body.cookie;
    if (!roblosecurityCookie) {
        return res.status(400).json({ success: false, error: "No cookie provided." });
    }

    const authTicket = await generateAuthTicket(roblosecurityCookie);
    if (!authTicket) {
        return res.status(400).json({ success: false, error: "Invalid or expired cookie." });
    }

    const redemptionResult = await redeemAuthTicket(authTicket);
    if (!redemptionResult.success) {
        return res.status(400).json({ success: false, error: "Failed to redeem authentication ticket." });
    }

    res.json({ success: true, newCookie: redemptionResult.refreshedCookie });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
