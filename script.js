// Variables globales
<<<<<<< HEAD
let temperature = [];
let humidite = [];
let luminosite = [];
let son = [];
let fumee = [];
let alerte = [];
=======
let temperature;
let humidite;
let luminosite;
let alerte;
let niveau_sonore;
>>>>>>> d517d16e71832fe45c71d164579097fb0bfaf750



// Fonction fetch all data attention sensible à utiliser quand trop de valeurs dans la base
async function fetchAllData() { 
    const reponse = await fetch("http://192.168.1.28:3000/all");
    const valeur_JSON = await reponse.json();

    console.log(valeur_JSON); // DEBUG

}
// Fonction fetch 5 dernières valeurs (affichage tableau)
async function LastValue() {
    const reponse = await fetch("http://192.168.1.28:3000/LastValue");
    const valeur_JSON = await reponse.json();
    
<<<<<<< HEAD
    // Extraction des données de la BDD premiere valeur
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
    const reponse = await fetch("http://192.168.1.28:3000/fiveLastValue");
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
=======
    // Extraction des données de la BDD
    temperature = valeur_JSON[0].temperature;
    humidite = valeur_JSON[0].humidity;
    luminosite = valeur_JSON[0].light_level;
    niveau_sonore = valeur_JSON[0].audio_level;
    alerte = valeur_JSON[0].alerte;
    
>>>>>>> d517d16e71832fe45c71d164579097fb0bfaf750

    console.log(valeur_JSON); // DEBUG

}

// Fonnction de mise à jour des dernières données mesuréespage web
function UpdateData(){
<<<<<<< HEAD
    TempJG.refresh(temperature[0]); // Jauge Temperature
    HumJG.refresh(humidite[0]); // Jauge humidite
    LumJG.refresh(luminosite[0]); // Jauge Luminosité
    SonJG.refresh(son[0]); // Jauge Son
=======
    TempJG.refresh(temperature); // Jauge Temperature
    SonJG.refresh(niveau_sonore); // Jauge Son
    HumJG.refresh(humidite); // Jauge humidite
    LumJG.refresh(luminosite); // Jauge Luminosité

>>>>>>> d517d16e71832fe45c71d164579097fb0bfaf750
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

setInterval(fiveLast, 3000);
setInterval(UpdateData, 500);
