// Variables globales
let temperature = [];
let humidite = [];
let luminosite = [];
let son = [];
let fumee = [];
let alerte = [];

let tempData = []; // Pour graphique
let humData = []; // Pour Graphique
let lightData = []; //Pour Graphique

// Fonction fetch all data attention sensible à utiliser quand trop de valeurs dans la base
async function fetchAllData() {
    const reponse = await fetch("http://192.168.1.28:3000/all");
    const valeur_JSON = await reponse.json();
    console.log(valeur_JSON); // DEBUG
}

// Fonction fetch 5 dernières valeurs (affichage tableau)
async function LastValue() {
    const reponse = await fetch("http://192.168.1.25:3000/LastValue");
    const valeur_JSON = await reponse.json();

    // Extraction des données de la BDD première valeur
    temperature[0] = valeur_JSON[0].temperature;
    humidite[0] = valeur_JSON[0].humidity;
    luminosite[0] = valeur_JSON[0].light_level;
    son[0] = valeur_JSON[0].audio_level;
    fumee[0] = valeur_JSON[0].smoke_presence;
    alerte[0] = valeur_JSON[0].alerte;
    console.log(valeur_JSON); // DEBUG
}

// Fonction fetch 5 dernières valeurs (affichage tableau)
async function fiveLast() {
    const reponse = await fetch("http://192.168.1.25:3000/fiveLastValue");
    const valeur_JSON = await reponse.json();

    // Boucle pour parcourir les 5 dernières valeurs et les assigner
    for (let i = 0; i < 5; i++) {
        temperature[i] = valeur_JSON[i].temperature;
        humidite[i] = valeur_JSON[i].humidity;
        luminosite[i] = valeur_JSON[i].light_level;
        son[i] = valeur_JSON[i].audio_level;
        fumee[i] = valeur_JSON[i].smoke_presence;
        alerte[i] = valeur_JSON[i].alerte;
    }

    // Mise à jour des données des graphiques
    tempData = temperature.slice();
    humData = humidite.slice();
    lightData = luminosite.slice();

    // Mise à jour des graphiques
    temperatureChart.data.datasets[0].data = tempData;
    humidityChart.data.datasets[0].data = humData;
    lightChart.data.datasets[0].data = lightData;

    // Actualiser les graphiques
    temperatureChart.update();
    humidityChart.update();
    lightChart.update();

    console.log(valeur_JSON); // DEBUG
}

// Fonction de mise à jour des dernières données mesurées page web Jauges
function UpdateData() {
    TempJG.refresh(temperature[0]); // Jauge Temperature
    HumJG.refresh(humidite[0]); // Jauge humidite
    LumJG.refresh(luminosite[0]); // Jauge Luminosité
    SonJG.refresh(son[0]); // Jauge Son
}

// Affichage des jauges

// Temperature
let infoTempJG = {
    id: "TempJauge",
    value: 0,
    min: -20,
    max: 60,
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
    hideInnerShadow: true,
    customSectors: [
        {
            color: "#93fff7", // Permet de changer les couleurs selon les valeurs | BLEU
            lo: -20,            // On veut du bleu pour froid, vert OK et rouge chaud
            hi: 17
        },
        {
            color: "#00ff00", // VERT
            lo: 17,
            hi: 25
        },
        {
            color: "#00FF00", // ROUGE
            lo: 25,
            hi: 60
        }
    ]
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
    hideInnerShadow: true,
    customSectors: [
        {
            color: "#FF0000", // Permet de changer les couleurs selon les valeurs
            lo: 0,            // On veut du vert à 100% et du rouge à 0 mais c'est l'inverse par défaut
            hi: 40
        },
        {
            color: "#FFFF00",
            lo: 40,
            hi: 60
        },
        {
            color: "#00FF00",
            lo: 60,
            hi: 100
        }
    ]
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

// Initialisation des graphiques
document.addEventListener("DOMContentLoaded", function() {
    const ctxTemp = document.getElementById("temperatureChart").getContext("2d");
    const ctxHum = document.getElementById("humidityChart").getContext("2d");
    const ctxLight = document.getElementById("lightChart").getContext("2d");

    // Créer les graphiques avec des données initiales
    window.temperatureChart = new Chart(ctxTemp, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"], // Labels fixes pour l'exemple
            datasets: [{
                label: "Température",
                data: tempData, // Données stockées
                borderColor: "red",
                borderWidth: 2
            }]
        }
    });

    window.humidityChart = new Chart(ctxHum, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"], // Labels fixes pour l'exemple
            datasets: [{
                label: "Humidité",
                data: humData, // Données stockées
                borderColor: "blue",
                borderWidth: 2
            }]
        }
    });

    window.lightChart = new Chart(ctxLight, {
        type: "line",
        data: {
            labels: ["1", "2", "3", "4", "5"], // Labels fixes pour l'exemple
            datasets: [{
                label: "Luminosité",
                data: lightData, // Données stockées
                borderColor: "yellow",
                borderWidth: 2
            }]
        }
    });
});

setInterval(fiveLast, 3000);
setInterval(UpdateData, 500);
