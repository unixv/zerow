/* Atrium Homes: lightweight browser UI; server controls all coins and inventory. */
(() => {
  "use strict";
  const root = document.querySelector("#homesOverlay");
  const byId = id => document.getElementById(id);
  const icons = {chair:"🪑", plant:"🌿", lamp:"💡", table:"☕", rug:"🧶",
                 sofa:"🛋", books:"📚", flower:"🌷"};
  let model = null, selectedRoomId = null, room = null, chosenItem = null;
  let running = false;
  function text(id, value){byId(id).textContent = value;}
  function status(value){text("homesStatus", value);}
  async function request(path, method="GET", data){
    const response = await fetch(path, {
      method, credentials:"same-origin", headers:{"Content-Type":"application/json"},
      ...(method==="GET"?{}:{body:JSON.stringify(data||{})})
    });
    const body = await response.json().catch(()=>({error:"Server error"}));
    if(!response.ok)throw Error(body.error||"Request failed");
    return body;
  }
  function makeButton(label, click, pressed=false){
    const b=document.createElement("button");b.type="button";b.textContent=label;
    if(pressed!==null)b.setAttribute("aria-pressed",String(pressed));
    b.addEventListener("click",click);return b;
  }
  function clear(el){el.replaceChildren();}
  function coinLabel(){return model ? model.coins + " coins" : "— coins";}
  async function reloadRoom(){
    if(!selectedRoomId){room=null;renderRoom();return;}
    room=await request("/api/homes/"+selectedRoomId);
    renderRoom();
  }
  async function reloadAll(){
    model=await request("/api/homes");
    if(selectedRoomId && !model.rooms.some(r=>r.id===selectedRoomId) &&
       !model.mine.some(r=>r.id===selectedRoomId))selectedRoomId=null;
    if(!selectedRoomId && model.mine.length)selectedRoomId=model.mine[0].id;
    if(!selectedRoomId && model.rooms.length)selectedRoomId=model.rooms[0].id;
    renderCatalog();renderRooms();
    await reloadRoom();renderInventory();
  }
  function renderCatalog(){
    text("homesWallet",coinLabel());
    const claim=byId("claimCoins");
    claim.disabled=model.next_claim>0;
    claim.textContent=model.next_claim>0?"Next reward tomorrow":"Claim +100 daily coins";
    text("newRoomPrice",model.mine.length?"Additional room: "+model.room_cost+" coins":"Your first room is free");
    byId("createHomeForm").querySelector("button").disabled=model.mine.length>=model.max_rooms;
    const shop=byId("homesShop");clear(shop);
    for(const item of model.catalog){
      const b=makeButton((icons[item.sku]||"✦")+" "+item.name,async()=>{
        if(running)return;
        running=true;
        try{
          const result=await request("/api/homes/buy","POST",{sku:item.sku});
          chosenItem=result.item_id;
          await reloadAll();status("Bought "+item.name+". Select an empty tile to place it.");
        }catch(e){status(e.message);}finally{running=false;}
      },null);
      const price=document.createElement("span");price.className="price";price.textContent=item.price+" coins";
      b.append(price);b.disabled=model.coins<item.price;
      shop.append(b);
    }
  }
  function renderRooms(){
    const list=byId("homesRooms");clear(list);
    if(!model.rooms.length){const p=document.createElement("p");p.textContent="No rooms yet. Create the first one.";list.append(p);}
    const shown=[...model.rooms];
    for(const mine of model.mine)if(!shown.some(room=>room.id===mine.id))shown.unshift({...mine,owner:me,furniture_count:0});
    for(const entry of shown){
      const b=makeButton(entry.name+" · "+entry.owner,async()=>{
        selectedRoomId=entry.id;chosenItem=null;
        try{await reloadRoom();renderRooms();renderInventory();status("");}
        catch(e){status(e.message);}
      },selectedRoomId===entry.id);
      b.title=entry.furniture_count+" decorations";
      list.append(b);
    }
  }
  function renderInventory(){
    const inventory=byId("homesInventory");clear(inventory);
    const items=model.inventory;
    if(!items.length){const p=document.createElement("p");p.textContent="Buy furnishings from the shop to start decorating.";inventory.append(p);}
    for(const item of items){
      const cat=model.catalog.find(x=>x.sku===item.sku);
      const title=(icons[item.sku]||"✦")+" "+(cat?.name||item.sku);
      const placed=item.room_id!==null;
      const b=makeButton(title+(placed?" · Placed":""),()=>{
        chosenItem=item.id;
        renderInventory();status("Furniture selected. Choose an empty tile in your own room.");
      },chosenItem===item.id);
      b.dataset.placed=String(placed);b.disabled=placed||!room?.room.editable;
      inventory.append(b);
    }
  }
  function renderRoom(){
    const canvas=byId("homeGrid");clear(canvas);
    if(!room){
      text("homesRoomTitle","Choose a room");
      text("homesRoomOwner","Create a room or visit another player's home.");
      canvas.classList.add("homes-empty");canvas.textContent="Rooms start with an empty floor. Make it yours.";
      return;
    }
    canvas.classList.remove("homes-empty");
    text("homesRoomTitle",room.room.name);
    text("homesRoomOwner",room.room.editable?"Your room · click furniture to pick it up":
         "Visiting "+room.room.owner+"'s room · view only");
    const occupied=new Map(room.items.map(item=>[item.x+","+item.y,item]));
    const width=room.room.width,height=room.room.height;
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      const item=occupied.get(x+","+y);
      const cat=item?model.catalog.find(p=>p.sku===item.sku):null;
      const label=item ? "Pick up "+(cat?.name||item.sku)+" at "+x+","+y :
                     "Tile "+x+","+y;
      const b=makeButton(item?(icons[item.sku]||"✦"):"",async()=>{
        if(running||!room?.room.editable)return;
        running=true;
        try{
          if(item){
            await request("/api/homes/pickup","POST",{room_id:room.room.id,item_id:item.id});
            status("Picked up "+(cat?.name||item.sku)+". It's back in your inventory.");
          }else{
            if(!chosenItem){status("Select furniture from your inventory before choosing a tile.");return;}
            await request("/api/homes/place","POST",
                           {room_id:room.room.id,item_id:chosenItem,x,y});
            chosenItem=null;status("Furniture placed. Other players can visit and see it.");
          }
          await reloadAll();
        }catch(e){status(e.message);}finally{running=false;}
      },null);
      b.setAttribute("aria-label",label);
      b.dataset.filled=String(!!item);
      if(!room.room.editable)b.disabled=true;
      canvas.append(b);
    }
  }
  async function open(){
    if(typeof me==="undefined"||!me){notify("Log in to explore player rooms.");return;}
    root.hidden=false;status("Loading rooms…");byId("closeHomes").focus();
    try{await reloadAll();status("Create a room, buy furniture, and place it on tiles.");}
    catch(e){status(e.message);}
  }
  function close(){root.hidden=true;byId("openRooms").focus();}
  byId("openRooms").addEventListener("click",open);
  byId("closeHomes").addEventListener("click",close);
  byId("createHomeForm").addEventListener("submit",async e=>{
    e.preventDefault();if(running)return;
    running=true;
    try{
      const name=byId("newHomeName").value.trim();
      const result=await request("/api/homes/create","POST",{name});
      selectedRoomId=result.room_id;chosenItem=null;
      byId("newHomeName").value="";
      await reloadAll();status("Room created! It's public, and you can decorate it.");
    }catch(error){status(error.message);}finally{running=false;}
  });
  byId("claimCoins").addEventListener("click",async()=>{
    if(running)return;running=true;
    try{
      const result=await request("/api/homes/claim","POST",{});
      await reloadAll();status("Claimed "+result.awarded+" coins.");
    }catch(e){status(e.message);}finally{running=false;}
  });
  root.addEventListener("keydown",e=>{
    if(e.key==="Escape"){e.preventDefault();e.stopPropagation();close();return;}
    if(e.key==="Tab"){
      const focusable=[...root.querySelectorAll("button:not(:disabled),input:not(:disabled)")].filter(el=>el.getClientRects().length);
      const first=focusable[0],last=focusable[focusable.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  });
  // A separate capture handler keeps movement keys from affecting the plaza
  // while editing rooms or using the furniture store.
  document.addEventListener("keydown",e=>{
    if(!root.hidden && ["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","w","a","s","d"].includes(e.key)){
      e.stopPropagation();
    }
  },true);
  byId("logout").addEventListener("click",close);
  setInterval(()=>{if(!root.hidden&&typeof me!=="undefined"&&!me)close();},2000);
})();
