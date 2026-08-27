//+------------------------------------------------------------------+
//|                                     RangeReversalScanner.mq5     |
//|  Detector dos Padroes 1 e 2 de reversao em Range Bars.           |
//|                                                                  |
//|  IMPORTANTE — leia antes de usar:                                |
//|  A investigacao estatistica (ver RELATORIO.md) NAO encontrou     |
//|  vantagem preditiva nestes padroes. Este indicador NAO emite     |
//|  score de probabilidade, por decisao deliberada.                 |
//|                                                                  |
//|  Ele serve para (a) visualizar as ocorrencias e (b) gravar as    |
//|  features em CSV para validacao forward genuina fora da amostra  |
//|  ja estudada.                                                    |
//|                                                                  |
//|  Convencoes replicadas do pipeline Python (src/lib.py e          |
//|  src/03_features.py):                                            |
//|    TICKVOL -> agressao compradora   (tick_volume no MT5)         |
//|    VOL     -> agressao vendedora    (real_volume no MT5)         |
//|    SPREAD  -> duracao da barra em ms (spread no MT5)             |
//|    time[]  -> timestamp de FECHAMENTO da barra                   |
//+------------------------------------------------------------------+
#property copyright "Estudo XAUUSD Pivo Range"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   2

#property indicator_label1  "Reversao de alta"
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrDodgerBlue
#property indicator_width1  2

#property indicator_label2  "Reversao de baixa"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrOrangeRed
#property indicator_width2  2

//--- entradas
input bool   InpEnableP1        = true;   // Detectar Padrao 1 (2 + reversao fraca)
input bool   InpEnableP2        = true;   // Detectar Padrao 2 (impulso + reversao forte)
input double InpP1MaxBodyRatio  = 0.50;   // P1: BodyRatio maximo da barra de reversao
input double InpP2MinBodyPrev   = 0.70;   // P2: BodyRatio minimo da 2a barra
input double InpP2MinBodyRev    = 0.70;   // P2: BodyRatio minimo da barra de reversao
input bool   InpLogToCSV        = false;  // Gravar features em CSV (MQL5/Files)
input string InpLogFileName     = "range_reversal_log.csv";
input bool   InpAlertOnSignal   = false;  // Alerta ao fechar barra de sinal

//--- buffers
double BufUp[];
double BufDown[];

//--- estado do logging
int    gLogHandle = INVALID_HANDLE;
datetime gLastLogged = 0;

//--- janelas usadas pelas features de regime (iguais ao Python)
#define WIN_MED20   20
#define WIN_MED50   50
#define MIN_BARS    (WIN_MED50 + 5)

//+------------------------------------------------------------------+
int OnInit()
  {
   SetIndexBuffer(0, BufUp,   INDICATOR_DATA);
   SetIndexBuffer(1, BufDown, INDICATOR_DATA);
   PlotIndexSetInteger(0, PLOT_ARROW, 233);   // seta para cima
   PlotIndexSetInteger(1, PLOT_ARROW, 234);   // seta para baixo
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   ArraySetAsSeries(BufUp,   false);
   ArraySetAsSeries(BufDown, false);

   IndicatorSetString(INDICATOR_SHORTNAME, "RangeReversalScanner");

   if(InpLogToCSV)
     {
      gLogHandle = FileOpen(InpLogFileName, FILE_WRITE|FILE_READ|FILE_CSV|FILE_ANSI, ',');
      if(gLogHandle == INVALID_HANDLE)
         Print("RangeReversalScanner: falha ao abrir ", InpLogFileName,
               " erro=", GetLastError());
      else
        {
         FileSeek(gLogHandle, 0, SEEK_END);
         if(FileTell(gLogHandle) == 0)
            FileWrite(gLogHandle,
               "close_time","pattern","side","close","R",
               "br0","br1","br2","wick0","openpos0","run_prev",
               "aggdn0","aggdn1","daggdn","diverg0",
               "aggt0","aggt_rel0","aggt_ratio01","agg_per_R",
               "dur0","dur_rel0","dur_rel50","dur_ratio01","intens0","intens_rel",
               "regime_dur","regime_aggt","hour","dow");
        }
     }
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(gLogHandle != INVALID_HANDLE)
     {
      FileClose(gLogHandle);
      gLogHandle = INVALID_HANDLE;
     }
  }

//+------------------------------------------------------------------+
//| Helpers — replicam exatamente as formulas do Python               |
//+------------------------------------------------------------------+
int BarDir(const double &open[], const double &close[], const int i)
  {
   if(close[i] > open[i]) return( 1);
   if(close[i] < open[i]) return(-1);
   return(0);
  }

double BarRange(const double &high[], const double &low[], const int i)
  {
   return(high[i] - low[i]);
  }

double BodyRatio(const double &open[], const double &high[],
                 const double &low[], const double &close[], const int i)
  {
   double r = BarRange(high, low, i);
   if(r <= 0.0) return(0.0);
   return(MathAbs(close[i] - open[i]) / r);
  }

//--- mediana causal de uma janela terminando em i (inclusive)
double RollMedian(const double &src[], const int i, const int win)
  {
   if(i + 1 < win) return(0.0);
   double tmp[];
   ArrayResize(tmp, win);
   for(int k = 0; k < win; k++)
      tmp[k] = src[i - win + 1 + k];
   ArraySort(tmp);
   if(win % 2 == 1) return(tmp[win / 2]);
   return(0.5 * (tmp[win / 2 - 1] + tmp[win / 2]));
  }

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   if(rates_total < MIN_BARS) return(0);

   int start = prev_calculated - 1;
   if(start < MIN_BARS) start = MIN_BARS;

   // series auxiliares para as medianas moveis (duracao e agressao total)
   static double sDur[];
   static double sAggT[];
   static double sIntens[];
   if(ArraySize(sDur) != rates_total)
     {
      ArrayResize(sDur,    rates_total);
      ArrayResize(sAggT,   rates_total);
      ArrayResize(sIntens, rates_total);
      start = MIN_BARS;   // recalcula tudo se o buffer mudou de tamanho
     }
   for(int i = MathMax(0, start - MIN_BARS); i < rates_total; i++)
     {
      sDur[i]    = (double)spread[i] / 1000.0;                 // segundos
      sAggT[i]   = (double)tick_volume[i] + (double)volume[i];
      sIntens[i] = sAggT[i] / MathMax(sDur[i], 0.5);
     }

   // A ULTIMA barra (rates_total-1) ainda esta em formacao: nunca gera sinal.
   int last = rates_total - 2;

   for(int i = start; i <= last; i++)
     {
      BufUp[i]   = EMPTY_VALUE;
      BufDown[i] = EMPTY_VALUE;

      int d0 = BarDir(open, close, i);
      int d1 = BarDir(open, close, i - 1);
      int d2 = BarDir(open, close, i - 2);
      if(d0 == 0 || d1 == 0 || d2 == 0) continue;

      // estrutura comum aos dois padroes
      if(d2 != d1)  continue;
      if(d0 != -d1) continue;

      double br0 = BodyRatio(open, high, low, close, i);
      double br1 = BodyRatio(open, high, low, close, i - 1);
      double br2 = BodyRatio(open, high, low, close, i - 2);

      bool isP1 = InpEnableP1 && (br0 <= InpP1MaxBodyRatio);
      bool isP2 = InpEnableP2 && (br1 >= InpP2MinBodyPrev) && (br0 >= InpP2MinBodyRev);
      if(!isP1 && !isP2) continue;

      // P1 e P2 sao mutuamente exclusivos com os defaults (0.50 vs 0.70).
      // Se o usuario afrouxar os limiares, P2 tem precedencia na marcacao.
      string pat = isP2 ? "P2" : "P1";

      if(d0 > 0) BufUp[i]   = low[i]  - BarRange(high, low, i) * 0.25;
      else       BufDown[i] = high[i] + BarRange(high, low, i) * 0.25;

      if(InpAlertOnSignal && i == last && time[i] != gLastLogged)
         Alert(StringFormat("%s: reversao de %s em %s @ %s",
               pat, (d0 > 0 ? "alta" : "baixa"), _Symbol,
               DoubleToString(close[i], _Digits)));

      if(gLogHandle != INVALID_HANDLE && time[i] > gLastLogged)
        {
         LogSignal(pat, d0, i, time, open, high, low, close,
                   tick_volume, volume, sDur, sAggT, sIntens);
         gLastLogged = time[i];
        }
     }

   // limpa a barra em formacao
   if(rates_total >= 1)
     {
      BufUp[rates_total - 1]   = EMPTY_VALUE;
      BufDown[rates_total - 1] = EMPTY_VALUE;
     }

   return(rates_total);
  }

//+------------------------------------------------------------------+
//| Grava as features do sinal — mesmas formulas de src/03_features.py|
//+------------------------------------------------------------------+
void LogSignal(const string pat, const int side, const int i,
               const datetime &time[], const double &open[],
               const double &high[], const double &low[], const double &close[],
               const long &tick_volume[], const long &volume[],
               const double &sDur[], const double &sAggT[], const double &sIntens[])
  {
   double R    = BarRange(high, low, i);
   double br0  = BodyRatio(open, high, low, close, i);
   double br1  = BodyRatio(open, high, low, close, i - 1);
   double br2  = BodyRatio(open, high, low, close, i - 2);

   // wick oposto ao fechamento, normalizado
   double wick = (side > 0) ? (open[i] - low[i]) : (high[i] - open[i]);
   double wick0 = (R > 0.0) ? wick / R : 0.0;
   double openpos0 = (R > 0.0) ? (open[i] - low[i]) / R : 0.0;

   // n de barras consecutivas na mesma direcao terminando em i-1
   int runPrev = 1;
   int dref = BarDir(open, close, i - 1);
   for(int k = i - 2; k >= 1; k--)
     {
      if(BarDir(open, close, k) == dref) runPrev++;
      else break;
     }

   // agressao
   double buy0  = (double)tick_volume[i],   sell0 = (double)volume[i];
   double buy1  = (double)tick_volume[i-1], sell1 = (double)volume[i-1];
   double aggt0 = buy0 + sell0, aggt1 = buy1 + sell1;
   double aggdn0_raw = (aggt0 > 0.0) ? (buy0 - sell0) / aggt0 : 0.0;
   double aggdn1_raw = (aggt1 > 0.0) ? (buy1 - sell1) / aggt1 : 0.0;
   double aggdn0 = aggdn0_raw * side;          // alinhado ao lado do trade
   double aggdn1 = aggdn1_raw * side;
   double daggdn = (aggdn0_raw - aggdn1_raw) * side;
   double diverg0 = aggdn0_raw * side;         // side == DIR[i] na barra de reversao

   double aggtMed20 = RollMedian(sAggT, i,     WIN_MED20);
   double aggtMed50 = RollMedian(sAggT, i,     WIN_MED50);
   double aggt_rel0 = aggt0 / MathMax(aggtMed20, 1.0);
   double aggt_ratio01 = aggt0 / MathMax(aggt1, 1.0);
   double agg_per_R = (R > 0.0) ? aggt0 / R : 0.0;

   // tempo
   double dur0 = sDur[i], dur1 = sDur[i-1];
   double durMed20 = RollMedian(sDur, i, WIN_MED20);
   double durMed50 = RollMedian(sDur, i, WIN_MED50);
   double dur_rel0    = dur0 / MathMax(durMed20, 0.5);
   double dur_rel50   = dur0 / MathMax(durMed50, 0.5);
   double dur_ratio01 = dur0 / MathMax(dur1, 0.5);
   double intensMed20 = RollMedian(sIntens, i, WIN_MED20);
   double intens_rel  = sIntens[i] / MathMax(intensMed20, 1e-6);

   MqlDateTime mt;
   TimeToStruct(time[i], mt);

   FileWrite(gLogHandle,
      TimeToString(time[i], TIME_DATE|TIME_SECONDS),
      pat, IntegerToString(side),
      DoubleToString(close[i], _Digits), DoubleToString(R, _Digits),
      DoubleToString(br0, 6), DoubleToString(br1, 6), DoubleToString(br2, 6),
      DoubleToString(wick0, 6), DoubleToString(openpos0, 6),
      IntegerToString(runPrev),
      DoubleToString(aggdn0, 6), DoubleToString(aggdn1, 6),
      DoubleToString(daggdn, 6), DoubleToString(diverg0, 6),
      DoubleToString(MathLog(1.0 + aggt0), 6),
      DoubleToString(aggt_rel0, 6), DoubleToString(aggt_ratio01, 6),
      DoubleToString(agg_per_R, 6),
      DoubleToString(MathLog(1.0 + dur0), 6),
      DoubleToString(dur_rel0, 6), DoubleToString(dur_rel50, 6),
      DoubleToString(dur_ratio01, 6),
      DoubleToString(MathLog(1.0 + sIntens[i]), 6),
      DoubleToString(intens_rel, 6),
      DoubleToString(MathLog(1.0 + durMed20), 6),
      DoubleToString(MathLog(1.0 + aggtMed20), 6),
      IntegerToString(mt.hour), IntegerToString(mt.day_of_week));

   FileFlush(gLogHandle);
  }
//+------------------------------------------------------------------+
