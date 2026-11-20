/* Atrium Homes: lightweight browser UI; server controls all coins and inventory. */
(() => {
  "use strict";
  const root = document.querySelector("#homesOverlay");
  const byId = id => document.getElementById(id);
  const icons = {chair:"🪑", plant:"🌿", lamp:"💡", table:"☕", rug:"🧶",
                 sofa:"🛋", books:"📚", flower:"🌷"};
  let model = null, selectedRoomId = null, room = null, chosenItem = null;
  let running = false, socialTimer = null, socialRoom = null, socialPending = false;
  let walkers = [], walking = false, roomGeneration = 0;
  const avatarLayer = document.createElement("div");
  avatarLayer.className = "homes-avatar-layer";
  avatarLayer.setAttribute("aria-label", "Players walking in this room");
  function paintWalkers(){
    avatarLayer.replaceChildren();
    for(const person of walkers){
      if(!Number.isInteger(person.x)||!Number.isInteger(person.y))continue;
      const avatar=document.createElement("span");
      avatar.className="homes-walker"+(person.self?" homes-walker-self":"");
      avatar.style.left=((person.x+.5)*10)+"%";
      avatar.style.top=((person.y+.5)*100/7)+"%";
      // Colors are only accepted as CSS hex colors, never HTML.
      const colors={moss:"#6cc4a0",ocean:"#68b9e9",sunset:"#f19b74",violet:"#b6a0f5",gold:"#efcb76",rose:"#e994b7"};
      avatar.style.setProperty("--walker-color",colors[person.avatar_color]||"#8fc9bc");
      avatar.textContent=person.name.slice(0,2).toUpperCase();
      avatar.title=person.name+" · "+person.avatar_style;
      avatar.setAttribute("aria-label",person.name+" at "+person.x+","+person.y);
      avatarLayer.append(avatar);
    }
  }
  async function walkTo(x,y){
    if(walking||!room||!selectedRoomId)return;
    const me=walkers.find(p=>p.self);
    if(!me){status("Waiting to join this room…");return;}
    const blocked=new Set(room.items.map(i=>i.x+","+i.y));
    if(blocked.has(x+","+y)){status("Furniture blocks that tile.");return;}
    const start=me.x+","+me.y,target=x+","+y;
    const queue=[[me.x,me.y]],visited=new Map([[start,null]]);
    for(let i=0;i<queue.length&&!visited.has(target);i++){
      const [cx,cy]=queue[i];
      for(const [dx,dy] of [[0,1],[1,0],[0,-1],[-1,0]]){
        const nx=cx+dx,ny=cy+dy,key=nx+","+ny;
        if(nx>=0&&nx<10&&ny>=0&&ny<7&&!blocked.has(key)&&!visited.has(key)){
          visited.set(key,[cx,cy]);queue.push([nx,ny]);
        }
      }
    }
    if(!visited.has(target)){status("No clear path to that tile.");return;}
    const path=[];
    for(let at=[x,y];at&&at.join(",")!==start;at=visited.get(at.join(",")))path.unshift(at);
    const id=selectedRoomId,generation=roomGeneration;
    walking=true;
    try{
      for(const [nx,ny] of path){
        if(root.hidden||selectedRoomId!==id||generation!==roomGeneration)break;
        await request("/api/homes/"+id+"/move","POST",{x:nx,y:ny});
        me.x=nx;me.y=ny;paintWalkers();
      }
      await refreshSocial();
    }catch(err){status(err.message);await refreshSocial();}
    finally{walking=false;}
  }
  const social = document.createElement("section");
  social.className = "homes-social";
  social.innerHTML = '<div class="homes-social-head"><h3>Room gathering</h3><span id="homesVisitorCount">0 here</span></div><div id="homesVisitors" class="homes-visitors" aria-label="Players in this room"></div><div id="homesRoomMessages" class="homes-roommessages" role="log" aria-label="Room conversation"></div><form id="homesChatForm" class="homes-chat"><input id="homesChatDraft" aria-label="Message this room" maxlength="280" autocomplete="off" placeholder="Say something to the room…" required><button type="submit">Send</button></form><p id="homesChatNotice" role="status"></p>';
  document.querySelector(".homes-main").append(social);
  function resetSocial(){
    socialRoom=null;walkers=[];roomGeneration++;avatarLayer.replaceChildren();
    byId("homesVisitors").replaceChildren();
    byId("homesRoomMessages").replaceChildren();
    delete byId("homesRoomMessages").dataset.signature;
    byId("homesVisitorCount").textContent="0 here";
    byId("homesChatNotice").textContent="";
  }
  async function enterRoom(){
    if(!selectedRoomId || root.hidden)return;
    const id=selectedRoomId;
    await request("/api/homes/"+id+"/visit","POST",{});
    if(selectedRoomId!==id || root.hidden)return;
    socialRoom=id;
    await refreshSocial();
  }
  async function refreshSocial(){
    if(root.hidden || !selectedRoomId || socialPending)return;
    socialPending=true;
    const id=selectedRoomId;
    try{
      await request("/api/homes/"+id+"/visit","POST",{});
      const data=await request("/api/homes/"+id+"/social");
      if(id!==selectedRoomId || root.hidden)return;
      walkers=data.visitors;
      paintWalkers();
      const visitors=byId("homesVisitors");
      visitors.replaceChildren();
      for(const person of data.visitors){
        const chip=document.createElement("span");
        chip.className="homes-visitor";
        chip.textContent=person.name;
        chip.title=person.avatar_color+" · "+person.avatar_style+" · tile "+person.x+","+person.y;
        visitors.append(chip);
      }
      byId("homesVisitorCount").textContent=data.visitors.length+" here";
      const log=byId("homesRoomMessages");
      const atBottom=log.scrollTop+log.clientHeight>=log.scrollHeight-25;
      const signature=data.messages.map(m=>m.id).join(",");
      if(log.dataset.signature!==signature){
        log.replaceChildren();
        for(const message of data.messages){
          const line=document.createElement("p");
          const name=document.createElement("strong");
          name.textContent=message.name+": ";
          line.append(name,document.createTextNode(message.body));
          log.append(line);
        }
        log.dataset.signature=signature;
        if(atBottom)log.scrollTop=log.scrollHeight;
      }
      byId("homesChatNotice").textContent="";
    }catch(e){if(!root.hidden)byId("homesChatNotice").textContent=e.message;}
    finally{socialPending=false;}
  }
  byId("homesChatForm").addEventListener("submit",async e=>{
    e.preventDefault();
    if(!selectedRoomId || running)return;
    const input=byId("homesChatDraft"),draft=input.value.trim();
    if(!draft)return;
    running=true;
    try{
      await request("/api/homes/"+selectedRoomId+"/chat","POST",{message:draft});
      if(input.value.trim()===draft)input.value="";
      await refreshSocial();
    }catch(err){byId("homesChatNotice").textContent=err.message;}
    finally{releaseBusy();}
  });
  socialTimer=setInterval(()=>{if(!root.hidden && selectedRoomId)refreshSocial();},3500);
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
    if(!selectedRoomId){room=null;renderRoom();resetSocial();return;}
    room=await request("/api/homes/"+selectedRoomId);
    renderRoom();
    await enterRoom();
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
  function releaseBusy(){
    running=false;
    document.querySelectorAll("#homesShop button").forEach(button=>{
      const price=Number(button.querySelector(".price")?.textContent.split(" ")[0]);
      button.disabled=Number.isFinite(price) && model.coins<price;
    });
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
        }catch(e){status(e.message);}finally{releaseBusy();}
      },null);
      const price=document.createElement("span");price.className="price";price.textContent=item.price+" coins";
      b.append(price);b.disabled=running||model.coins<item.price;
      shop.append(b);
    }
  }
  function jumpTo(selector){
    const target=document.querySelector(selector);
    if(target && window.matchMedia("(max-width:760px)").matches){
      target.scrollIntoView({block:"start",behavior:"instant"});
    }
  }
  function renderRooms(){
    const list=byId("homesRooms");clear(list);
    if(!model.rooms.length){const p=document.createElement("p");p.textContent="No rooms yet. Create the first one.";list.append(p);}
    const shown=[...model.rooms];
    for(const mine of model.mine)if(!shown.some(room=>room.id===mine.id))shown.unshift({...mine,owner:me,furniture_count:0});
    for(const entry of shown){
      const b=makeButton(entry.name+" · "+entry.owner,async()=>{
        selectedRoomId=entry.id;chosenItem=null;resetSocial();
        try{await reloadRoom();renderRooms();renderInventory();status("");jumpTo(".homes-main");}
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
    text("homesRoomOwner",room.room.editable?"Your room · tap an empty tile to walk, or select furniture to decorate":
         "Visiting "+room.room.owner+"'s room · tap empty tiles to walk together");
    const occupied=new Map(room.items.map(item=>[item.x+","+item.y,item]));
    const width=room.room.width,height=room.room.height;
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      const item=occupied.get(x+","+y);
      const cat=item?model.catalog.find(p=>p.sku===item.sku):null;
      const label=item ? "Pick up "+(cat?.name||item.sku)+" at "+x+","+y :
                     "Tile "+x+","+y;
      const b=makeButton(item?(icons[item.sku]||"✦"):"",async()=>{
        if(running)return;
        if(!room?.room.editable){
          if(!item)await walkTo(x,y);
          return;
        }
        running=true;
        try{
          if(item){
            await request("/api/homes/pickup","POST",{room_id:room.room.id,item_id:item.id});
            status("Picked up "+(cat?.name||item.sku)+". It's back in your inventory.");
          }else{
            if(!chosenItem){releaseBusy();await walkTo(x,y);return;}
            await request("/api/homes/place","POST",
                           {room_id:room.room.id,item_id:chosenItem,x,y});
            chosenItem=null;status("Furniture placed. Other players can visit and see it.");
          }
          await reloadAll();
        }catch(e){status(e.message);}finally{releaseBusy();}
      },null);
      b.setAttribute("aria-label",label);
      b.dataset.filled=String(!!item);
      if(!room.room.editable&&item)b.disabled=true;
      canvas.append(b);
    }
    canvas.append(avatarLayer);
    paintWalkers();
  }
  async function open(){
    if(typeof me==="undefined"||!me){notify("Log in to explore player rooms.");return;}
    root.hidden=false;status("Loading rooms…");byId("closeHomes").focus();
    try{await reloadAll();status("Create a room, buy furniture, and place it on tiles.");}
    catch(e){status(e.message);}
  }
  function close(){root.hidden=true;resetSocial();request("/api/homes/leave","POST",{}).catch(()=>{});byId("openRooms").focus();}
  byId("browseHomes").addEventListener("click",()=>jumpTo("#homesRooms"));
  byId("shopHomes").addEventListener("click",()=>jumpTo("#homesShop"));
  byId("viewHome").addEventListener("click",()=>jumpTo(".homes-main"));
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
    }catch(error){status(error.message);}finally{releaseBusy();}
  });
  byId("claimCoins").addEventListener("click",async()=>{
    if(running)return;running=true;
    try{
      const result=await request("/api/homes/claim","POST",{});
      await reloadAll();status("Claimed "+result.awarded+" coins.");
    }catch(e){status(e.message);}finally{releaseBusy();}
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
