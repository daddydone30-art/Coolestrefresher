const axios = require("axios");

async function generateAuthTicket(roblosecurityCookie) {
    try {
        let csrfToken = "";
        try {
            await axios.post("https://auth.roblox.com/v2/logout", {}, {
                headers: { 'Cookie': `.ROBLOSECURITY=${roblosecurityCookie}` }
            });
        } catch (error) {
            csrfToken = error.response?.headers["x-csrf-token"] || "";
        }

        if (!csrfToken) return null;

        const response = await axios.post("https://auth.roblox.com/v1/authentication-ticket", {}, {
            headers: {
                "x-csrf-token": csrfToken,
                "referer": "https://www.roblox.com/",
                "Content-Type": "application/json",
                "Cookie": `.ROBLOSECURITY=${roblosecurityCookie}`
            }
        });

        return response.headers['rbx-authentication-ticket'] || null;
    } catch (error) {
        return null;
    }
}

async function redeemAuthTicket(authTicket) {
    try {
        const response = await axios.post("https://auth.roblox.com/v1/authentication-ticket/redeem", {
            "authenticationTicket": authTicket
        }, {
            headers: { 'RBXAuthenticationNegotiation': '1' }
        });

        const setCookieHeader = response.headers['set-cookie']?.toString() || "";
        const match = setCookieHeader.match(/(_\|WARNING:-DO-NOT-SHARE-THIS[\s\S]*?)(?=;|$)/);

        if (match && match[1]) {
            return { success: true, refreshedCookie: match[1] };
        }
        return { success: false };
    } catch (error) {
        return { success: false };
    }
}

module.exports = { generateAuthTicket, redeemAuthTicket };
