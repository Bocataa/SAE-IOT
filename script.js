// Variables globales
let temperature;
let humidite;
let luminosite;
let alerte;
let niveau_sonore;

// Fonction fetch all data
async function fetchAllData() {
    const reponse = await fetch("http://192.168.1.25:3000/all");
    const valeur_JSON = await reponse.json();
    
    // Extraction des données de la BDD
    temperature = valeur_JSON[0].temperature;
    humidite = valeur_JSON[0].humidity;
    luminosite = valeur_JSON[0].light_level;
    niveau_sonore = valeur_JSON[0].audio_level;
    alerte = valeur_JSON[0].alerte;
    

    console.log(valeur_JSON); // DEBUG

}

// Fonnction de mise à jour des données page web

function UpdateData(){
    TempJG.refresh(temperature); // Jauge Temperature
    SonJG.refresh(niveau_sonore); // Jauge Son
    HumJG.refresh(humidite); // Jauge humidite
    LumJG.refresh(luminosite); // Jauge Luminosité

}

// Affichage des jauges

    // Temperature
    let infoTempJG = {
        id: "TempJauge",
        value: 0,
        min: -20,
        max: 70,
        decimals: 1,
        symbol: ' °C',
        donut: false,
        title: "Température",
        label: "mesuré",
        pointer: true,
        pointerOptions: {
            toplength: 10,
            bottomlength: 5,
            bottomwidth: 2
        },
        gaugeWidthScale: 0.9,
        counter: true,
        hideInnerShadow: true
    };

    let TempJG = new JustGage(infoTempJG);

    // Humidite
    let infoHumJG = {
        id: "HumJauge",
        value: 0,
        min: 0,
        max: 100,
        decimals: 1,
        symbol: ' %',
        donut: false,
        title: "Humidité",
        label: "mesuré",
        pointer: true,
        pointerOptions: {
            toplength: 10,
            bottomlength: 5,
            bottomwidth: 2
        },
        gaugeWidthScale: 0.9,
        counter: true,
        hideInnerShadow: true
    };

    let HumJG = new JustGage(infoHumJG);

    

    // Luminosite
    let infoLumJG = {
        id: "LumJauge",
        value: 0,
        min: 0,
        max: 100,
        decimals: 1,
        symbol: ' %',
        donut: false,
        title: "Luminosité",
        label: "mesuré",
        pointer: true,
        pointerOptions: {
            toplength: 10,
            bottomlength: 5,
            bottomwidth: 2
        },
        gaugeWidthScale: 0.9,
        counter: true,
        hideInnerShadow: true
    };

    let LumJG = new JustGage(infoLumJG);

    

    // Niveau Sonore
    let infoSonJG = {
        id: "SonJauge",
        value: 0,
        min: 0,
        max: 100,
        decimals: 1,
        symbol: ' %',
        donut: false,
        title: "Niveau Sonore",
        label: "mesuré",
        pointer: true,
        pointerOptions: {
            toplength: 10,
            bottomlength: 5,
            bottomwidth: 2
        },
        gaugeWidthScale: 0.9,
        counter: true,
        hideInnerShadow: true
    };

    let SonJG = new JustGage(infoSonJG);

    // On initialise à 0 toutes les jauges
    TempJG.refresh(0); // Jauge Temperature
    SonJG.refresh(0); // Jauge Son
    HumJG.refresh(0); // Jauge humidite
    LumJG.refresh(0); // Jauge Luminosité

// Affichage des graphiques

document.addEventListener("DOMContentLoaded", function() {
    const ctxTemp = document.getElementById("temperatureChart").getContext("2d");
    const ctxHum = document.getElementById("humidityChart").getContext("2d");
    const ctxLight = document.getElementById("lightChart").getContext("2d");

    new Chart(ctxTemp, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"],
            datasets: [{
                label: "Température",
                data: [22, 24, 23, 25, 26],
                borderColor: "red",
                borderWidth: 2
            }]
        }
    });

    new Chart(ctxHum, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"],
            datasets: [{
                label: "Humidité",
                data: [50, 52, 55, 57, 60],
                borderColor: "blue",
                borderWidth: 2
            }]
        }
    });

    new Chart(ctxLight, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"],
            datasets: [{
                label: "Luminosité",
                data: [300, 320, 310, 330, 340],
                borderColor: "yellow",
                borderWidth: 2
            }]
        }
    });
});

setInterval(fetchAllData, 1000);
setInterval(UpdateData, 500);
