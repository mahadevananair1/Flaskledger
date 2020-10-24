//Movement Animation to happen
const card = document.querySelector(".card");
const container = document.querySelector(".container");
//Items
const title = document.querySelector(".title");
const sneaker = document.querySelector(".sneaker img");
const purchase = document.querySelector(".purchase button");
const description = document.querySelector(".info h3");
const form_animate = document.querySelector(".inputcolumns");
console.log(form_animate);

//Moving Animation Event
card.addEventListener("mousemove", (e) => {
  let xAxis = (window.innerWidth / 2 - e.pageX) / 75;
  let yAxis = (window.innerHeight / 2 - e.pageY) / 75;
  card.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
});
//Animate In
card.addEventListener("mouseenter", (e) => {
  card.style.transition = "none";
  //Popout
  title.style.transform = "translateZ(150px)";
  sneaker.style.transform = "translateZ(200px) rotateZ(-45deg)";
  description.style.transform = "translateZ(125px)";
  form_animate.style.transform = "translateZ(100px)";
  purchase.style.transform = "translateZ(75px)";
  

});
//Animate Out
card.addEventListener("mouseleave", (e) => {
  card.style.transition = "all 0.5s ease";
  card.style.transform = `rotateY(0deg) rotateX(0deg)`;
  //Popback
  title.style.transform = "translateZ(0px)";
  sneaker.style.transform = "translateZ(0px) rotateZ(0deg)";
  description.style.transform = "translateZ(0px)";
  form_animate.style.transform = "translateZ(0px)";
  purchase.style.transform = "translateZ(0px)";
  
});
