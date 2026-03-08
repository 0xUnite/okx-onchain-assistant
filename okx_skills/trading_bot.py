"""
链上交易机器人
自动交易、止盈止损、仓位管理
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Position:
    """仓位"""
    id: str
    token: str
    chain: str
    side: str  # LONG/SHORT
    entry_price: float
    quantity: float
    leverage: int
    current_price: float
    pnl: float
    pnl_pct: float
    status: str  # OPEN/CLOSED
    stop_loss: float = None
    take_profit: float = None
    open_time: str = None
    close_time: str = None
    close_reason: str = None

class TradingBot:
    """链上交易机器人"""
    
    def __init__(self, max_position_size: float = 2.0):
        self.max_position_size = max_position_size  # 最大仓位（U）
        self.positions: List[Position] = []
        self.position_id = 0
    
    def open_position(self, token: str, chain: str, side: str, entry_price: float, 
                      quantity: float, leverage: int = 1, stop_loss: float = None,
                      take_profit: float = None) -> Dict:
        """开仓"""
        self.position_id += 1
        
        position = Position(
            id=str(self.position_id),
            token=token,
            chain=chain,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            current_price=entry_price,
            pnl=0,
            pnl_pct=0,
            status="OPEN",
            stop_loss=stop_loss,
            take_profit=take_profit,
            open_time=datetime.now().isoformat()
        )
        
        self.positions.append(position)
        
        # 模拟执行链上交易
        tx_hash = f"0x{''.join([f'{self.position_id:02x}' for _ in range(32)])}"
        
        return {
            "status": "success",
            "position_id": position.id,
            "token": token,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "leverage": leverage,
            "tx_hash": tx_hash,
            "message": f"✅ {side} {quantity} {token} @ {entry_price}",
            "timestamp": datetime.now().isoformat()
        }
    
    def close_position(self, position_id: str, close_price: float, reason: str = "manual") -> Dict:
        """平仓"""
        position = None
        for p in self.positions:
            if p.id == position_id and p.status == "OPEN":
                position = p
                break
        
        if not position:
            return {"status": "error", "message": "Position not found"}
        
        # 计算盈亏
        if position.side == "LONG":
            pnl = (close_price - position.entry_price) * position.quantity
            pnl_pct = (close_price / position.entry_price - 1) * 100
        else:
            pnl = (position.entry_price - close_price) * position.quantity
            pnl_pct = (position.entry_price / close_price - 1) * 100
        
        position.current_price = close_price
        position.pnl = pnl
        position.pnl_pct = pnl_pct * position.leverage
        position.status = "CLOSED"
        position.close_price = close_price
        position.close_time = datetime.now().isoformat()
        position.close_reason = reason
        
        return {
            "status": "success",
            "position_id": position.id,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "close_price": close_price,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_stop_loss_take_profit(self) -> List[Dict]:
        """检查止盈止损"""
        triggered = []
        
        for p in self.positions:
            if p.status != "OPEN":
                continue
            
            # 更新当前价格（模拟）
            from okx_skills.onchainos_api import get_price
            try:
                price_data = get_price(p.token, p.chain)
                p.current_price = price_data["price"]
            except Exception:
                p.current_price = p.entry_price  # 如果获取失败，使用入场价
            
            # 计算盈亏
            if p.side == "LONG":
                pnl_pct = (p.current_price / p.entry_price - 1) * 100 * p.leverage
            else:
                pnl_pct = (p.entry_price / p.current_price - 1) * 100 * p.leverage
            
            p.pnl_pct = pnl_pct
            p.pnl = p.entry_price * p.quantity * pnl_pct / 100
            
            # 检查止损
            if p.stop_loss:
                if (p.side == "LONG" and p.current_price <= p.stop_loss) or \
                   (p.side == "SHORT" and p.current_price >= p.stop_loss):
                    result = self.close_position(p.id, p.stop_loss, "SL")
                    triggered.append({"type": "STOP_LOSS", "position": p.id, **result})
                    continue
            
            # 检查止盈
            if p.take_profit:
                if (p.side == "LONG" and p.current_price >= p.take_profit) or \
                   (p.side == "SHORT" and p.current_price <= p.take_profit):
                    result = self.close_position(p.id, p.take_profit, "TP")
                    triggered.append({"type": "TAKE_PROFIT", "position": p.id, **result})
        
        return triggered
    
    def get_positions(self, status: str = None) -> List[Dict]:
        """获取仓位"""
        if status:
            return [asdict(p) for p in self.positions if p.status == status]
        return [asdict(p) for p in self.positions]
    
    def get_open_positions(self) -> List[Dict]:
        """获取未平仓位"""
        return self.get_positions("OPEN")
    
    def get_pnl_summary(self) -> Dict:
        """盈亏汇总"""
        closed = [p for p in self.positions if p.status == "CLOSED"]
        
        total_pnl = sum(p.pnl for p in closed)
        wins = len([p for p in closed if p.pnl > 0])
        losses = len([p for p in closed if p.pnl <= 0])
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "avg_pnl": round(total_pnl / total, 2) if total > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_position_size(self, account_balance: float, risk_pct: float, 
                                entry_price: float, stop_loss_price: float) -> float:
        """计算仓位大小"""
        risk_amount = account_balance * (risk_pct / 100)
        price_risk = abs(entry_price - stop_loss_price) / entry_price
        
        if price_risk == 0:
            return 0
        
        position_size = risk_amount / price_risk
        return min(position_size, self.max_position_size)


# ===== 便捷函数 =====

# 全局机器人实例
_bot = TradingBot()

def open_position(token: str, chain: str, side: str, entry_price: float, 
                  quantity: float, leverage: int = 1, stop_loss: float = None,
                  take_profit: float = None) -> Dict:
    """开仓"""
    return _bot.open_position(token, chain, side, entry_price, quantity, leverage, stop_loss, take_profit)

def close_position(position_id: str, close_price: float, reason: str = "manual") -> Dict:
    """平仓"""
    return _bot.close_position(position_id, close_price, reason)

def get_positions(status: str = None) -> List[Dict]:
    """获取仓位"""
    return _bot.get_positions(status)

def get_pnl_summary() -> Dict:
    """盈亏汇总"""
    return _bot.get_pnl_summary()


if __name__ == "__main__":
    bot = TradingBot()
    
    # 测试开仓
    print("=== 开仓测试 ===")
    result = bot.open_position("ETH", "ethereum", "LONG", 3000, 0.1, stop_loss=2850, take_profit=3300)
    print(result)
    
    print("\n=== 检查止盈止损 ===")
    triggered = bot.check_stop_loss_take_profit()
    print(f"触发: {len(triggered)} 个")
    
    print("\n=== 仓位列表 ===")
    print(bot.get_positions())
    
    print("\n=== 盈亏汇总 ===")
    print(bot.get_pnl_summary())
