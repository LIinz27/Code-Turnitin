const request = require('request');

const state = {
    ingredients: {
        rice: 500,
        eggs: 3,
        vegetables: 300,
        soySauce: 50,
    },
    isCooking: false,
    hargaPerPorsi: 10, // Harga per porsi nasi goreng dalam satuan mata uang (USD).
};

const checkAvailability = () => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (!state.isCooking) {
                resolve("Dapur siap digunakan.");
            } else {
                reject("Maaf, dapur sedang sibuk.");
            }
        }, 1000);
    });
};

const checkStock = () => {
    return new Promise((resolve, reject) => {
        state.isCooking = true;
        setTimeout(() => {
            if (
                state.ingredients.rice >= 100 &&
                state.ingredients.eggs >= 1 &&
                state.ingredients.vegetables >= 100 &&
                state.ingredients.soySauce >= 10
            ) {
                resolve("Bahan cukup. Bisa membuat nasi goreng.");
            } else {
                reject("Bahan tidak cukup!");
            }
        }, 1500);
    });
};

const cookNasiGoreng = () => {
    console.log("Memasak nasi goreng Anda...");
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve("Nasi goreng sudah siap!");
        }, 3000);
    });
};

const convertCurrency = (fromCurrency, toCurrency, amount) => {
    const url = `http://api.exchangeratesapi.io/v1/latest?access_key=005d47f747a8e7351c9178ea85faf8c9`;

    return new Promise((resolve, reject) => {
        request.get(url, (error, response, body) => {
            if (error) {
                reject('Failed to fetch exchange rates:', error);
            } else {
                try {
                    const data = JSON.parse(body);
                    if (data.rates) {
                        const fromRate = data.rates[fromCurrency];
                        const toRate = data.rates[toCurrency];
                        const convertedAmount = (amount / fromRate) * toRate;
                        resolve(convertedAmount);
                    } else {
                        reject('Error fetching exchange rates');
                    }
                } catch (parseError) {
                    reject('Error parsing API response:', parseError);
                }
            }
        });
    });
};

const calculateTotalPrice = (quantity) => {
    return state.hargaPerPorsi * quantity;
};

async function makeNasiGoreng(quantity) {
    try {
        const availabilityStatus = await checkAvailability();
        console.log(availabilityStatus);

        const [stockStatus, nasiGorengMessage] = await Promise.all([
            checkStock(),
            cookNasiGoreng()
        ]);

        console.log(stockStatus);
        console.log(nasiGorengMessage);

        const hargaPerPorsiIDR = await convertCurrency('USD', 'IDR', state.hargaPerPorsi);
        const totalPriceIDR = calculateTotalPrice(quantity) * hargaPerPorsiIDR;

        console.log(`Total harga untuk ${quantity} porsi nasi goreng: ${totalPriceIDR} IDR`);

        state.isCooking = false;
    } catch (error) {
        console.log(error);
        state.isCooking = false;
    }
}

const jumlahPorsi = 2; // Jumlah porsi nasi goreng yang ingin dibuat.
makeNasiGoreng(jumlahPorsi);
