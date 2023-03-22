var Gold = function(conf) {
	var gold = this;
	gold.id = conf.goldId;
	gold.x = conf.x;
	gold.y = conf.y;
	gold.z = Math.random() * 0.8 ;
	gold.size = 8;
	gold.opacity = 1;
	var offset = gold.size;
	gold.update = function(bounds,tadpoles) {
		if (!gold.hide){
			for(id in tadpoles) {
				var tadpole = tadpoles[id];
				if ((Math.abs(tadpole.x - gold.x) < offset) && (Math.abs(tadpole.y - gold.y) <offset )){
					gold.hide = true;
					tadpole.size = tadpole.size + 1;
					if (webSocketService){
						app.sendGoldMessage(gold,tadpole);
					}
				}
			}
		}
	};
	
	gold.draw = function(context) {
		if (!gold.hide){
			context.fillStyle = '#ffb300';
			context.beginPath();
			context.arc(gold.x, gold.y, this.z * this.size, 0, Math.PI*2);
			context.closePath();
			context.fill();
		}
	};
}
