//+------------------------------------------------------------------+
//| XAU_Levels_Opus.mq5                                              |
//| Draws the xau-opus skill's levels from a CSV written by Python   |
//| (scripts\draw.py).  File: MQL5\Files\levels_opus_<SYMBOL>.csv    |
//| Format per line:  price;label;kind    kind = S | R | P           |
//| Reloads the file every InpRefreshSec seconds.                    |
//| Own file and own object prefix (LVO_), dashed lines: it can sit  |
//| on the same chart as XAU_Levels without touching its drawing.    |
//+------------------------------------------------------------------+
#property copyright "ANS"
#property version   "1.00"
#property indicator_chart_window
#property indicator_plots 0

input int    InpRefreshSec = 5;          // reload interval (seconds)
input string InpFile       = "";         // file name (blank = levels_opus_<SYMBOL>.csv)
input color  InpColorS     = clrDodgerBlue;   // support
input color  InpColorR     = clrOrangeRed;    // resistance
input color  InpColorP     = clrGold;         // pivot / other
input int    InpWidth      = 1;
input ENUM_LINE_STYLE InpStyle = STYLE_DASH;
input bool   InpShowLabel  = true;

string   g_prefix = "LVO_";
string   g_file;
datetime g_lastMod = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   g_file = (InpFile == "") ? "levels_opus_" + _Symbol + ".csv" : InpFile;
   EventSetTimer(InpRefreshSec);
   LoadLevels();
   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, g_prefix);
}
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[],
                const double &open[], const double &high[], const double &low[], const double &close[],
                const long &tick_volume[], const long &volume[], const int &spread[])
{
   return rates_total;
}
//+------------------------------------------------------------------+
void OnTimer()
{
   LoadLevels();
}
//+------------------------------------------------------------------+
void LoadLevels()
{
   if(!FileIsExist(g_file)) return;
   datetime mod = (datetime)FileGetInteger(g_file, FILE_MODIFY_DATE);
   if(mod == g_lastMod) return;
   g_lastMod = mod;

   int h = FileOpen(g_file, FILE_READ | FILE_TXT | FILE_ANSI);
   if(h == INVALID_HANDLE) { Print("XAU_Levels_Opus: cannot open ", g_file, " err ", GetLastError()); return; }

   ObjectsDeleteAll(0, g_prefix);
   int n = 0;
   while(!FileIsEnding(h))
   {
      string line = FileReadString(h);
      StringTrimLeft(line); StringTrimRight(line);
      if(line == "" || StringGetCharacter(line, 0) == '#') continue;
      string parts[];
      int k = StringSplit(line, ';', parts);
      if(k < 1) continue;
      double price = StringToDouble(parts[0]);
      if(price <= 0) continue;
      string label = (k > 1) ? parts[1] : "";
      string kind  = (k > 2) ? parts[2] : "P";
      StringToUpper(kind);
      color c = (kind == "S") ? InpColorS : (kind == "R") ? InpColorR : InpColorP;
      string name = g_prefix + IntegerToString(n);
      if(ObjectCreate(0, name, OBJ_HLINE, 0, 0, price))
      {
         ObjectSetInteger(0, name, OBJPROP_COLOR, c);
         ObjectSetInteger(0, name, OBJPROP_WIDTH, InpWidth);
         ObjectSetInteger(0, name, OBJPROP_STYLE, InpStyle);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
         ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
         ObjectSetString(0, name, OBJPROP_TEXT, label);
         ObjectSetString(0, name, OBJPROP_TOOLTIP, label + " " + DoubleToString(price, _Digits));
      }
      if(InpShowLabel && label != "")
      {
         string tn = name + "t";
         datetime t = iTime(_Symbol, _Period, 0);
         if(ObjectCreate(0, tn, OBJ_TEXT, 0, t, price))
         {
            ObjectSetString(0, tn, OBJPROP_TEXT, " " + label);
            ObjectSetInteger(0, tn, OBJPROP_COLOR, c);
            ObjectSetInteger(0, tn, OBJPROP_FONTSIZE, 8);
            ObjectSetInteger(0, tn, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);
            ObjectSetInteger(0, tn, OBJPROP_SELECTABLE, false);
         }
      }
      n++;
   }
   FileClose(h);
   ChartRedraw();
   Print("XAU_Levels_Opus: drew ", n, " levels from ", g_file);
}
//+------------------------------------------------------------------+
