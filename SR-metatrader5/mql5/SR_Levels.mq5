//+------------------------------------------------------------------+
//|                                                   SR_Levels.mq5  |
//|  Desenha os niveis gerados pelo projeto SR-metatrader5 (Python).  |
//|                                                                  |
//|  O script Python grava um CSV por simbolo na pasta MQL5\Files:    |
//|                                                                  |
//|      SR_USDJPY.csv                                               |
//|      symbol;price;score;n_events;unique_days;unique_months;       |
//|      span_days;first_event;last_event                            |
//|                                                                  |
//|  Este indicador monta o nome do arquivo a partir do _Symbol do    |
//|  grafico, confere a coluna `symbol` do arquivo contra o simbolo   |
//|  do grafico e desenha uma OBJ_HLINE por nivel. Todas as linhas    |
//|  usam a mesma cor, espessura e estilo (definidos nos inputs).     |
//|                                                                  |
//|  Recarrega sozinho quando o Python regrava o arquivo.             |
//+------------------------------------------------------------------+
#property copyright "SR-metatrader5"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- limite de seguranca para o parser
#define SR_MAX_NIVEIS   500
#define SR_PREFIXO      "SRL_"

//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
input group "Arquivo";
input string InpPrefixo        = "SR_";        // Prefixo do arquivo (SR_ -> SR_USDJPY.csv)
input string InpArquivo        = "";           // Arquivo fixo (vazio = derivado do simbolo)
input string InpSimbolo        = "";           // Simbolo do arquivo (vazio = _Symbol)
input bool   InpPastaComum     = false;        // Ler da pasta Common em vez de MQL5\Files
input bool   InpConferirSimbolo= true;         // Recusar arquivo de outro simbolo
input int    InpRecarregarSeg  = 30;           // Recarregar a cada N segundos (0 = nunca)

input group "Filtro";
input double InpScoreMinimo    = 0.0;          // Score minimo (0 = todos)
input int    InpMaxLinhas      = 0;            // Maximo de linhas, as de maior score (0 = todas)

input group "Estilo";
input color           InpCor      = clrDodgerBlue;  // Cor das linhas
input int             InpEspessura= 1;              // Espessura
input ENUM_LINE_STYLE InpEstilo   = STYLE_DASH;     // Estilo
input bool            InpAoFundo  = true;           // Desenhar atras dos candles
input bool            InpRotulo   = true;           // Texto no fim da linha (score / toques)
input bool            InpSelecion = false;          // Permitir selecionar/arrastar

//+------------------------------------------------------------------+
//| Estado                                                           |
//+------------------------------------------------------------------+
string   g_arquivo   = "";     // nome resolvido do CSV
datetime g_modificado= 0;      // data de modificacao ja carregada
int      g_desenhadas= 0;
bool     g_avisado   = false;  // ja reclamou da ausencia do arquivo

//+------------------------------------------------------------------+
//| Um nivel lido do arquivo                                         |
//+------------------------------------------------------------------+
struct Nivel
  {
   double   price;
   double   score;
   int      n_events;
   int      unique_days;
   datetime last_event;
  };

//+------------------------------------------------------------------+
//| Substitui os caracteres proibidos em nome de arquivo no Windows,  |
//| exatamente como o sanitize_symbol() do config.py.                 |
//+------------------------------------------------------------------+
string SanitizarSimbolo(const string s)
  {
   string proibidos = "<>:\"/\\|?*";
   string saida = "";
   for(int i = 0; i < StringLen(s); i++)
     {
      string c = StringSubstr(s, i, 1);
      saida += (StringFind(proibidos, c) >= 0) ? "_" : c;
     }
   return saida;
  }

//+------------------------------------------------------------------+
//| Nome base do simbolo, sem o sufixo do broker.                     |
//| "USDJPY.m", "USDJPYc", "USDJPY-ECN" -> "USDJPY"                   |
//+------------------------------------------------------------------+
string SimboloBase(const string s)
  {
   int corte = StringLen(s);
   for(int i = 0; i < StringLen(s); i++)
     {
      ushort c = StringGetCharacter(s, i);
      bool letra = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
      bool digito = (c >= '0' && c <= '9');
      if(!letra && !digito && c != '$')
        {
         corte = i;
         break;
        }
     }
   string base = StringSubstr(s, 0, corte);
   StringToUpper(base);
   return base;
  }

//+------------------------------------------------------------------+
//| Dois simbolos designam o mesmo ativo?                             |
//+------------------------------------------------------------------+
bool MesmoSimbolo(const string a, const string b)
  {
   string x = a, y = b;
   StringTrimLeft(x); StringTrimRight(x);
   StringTrimLeft(y); StringTrimRight(y);
   StringToUpper(x);  StringToUpper(y);
   if(x == y)
      return true;
   return (SimboloBase(x) == SimboloBase(y) && SimboloBase(x) != "");
  }

//+------------------------------------------------------------------+
//| Resolve qual arquivo ler.                                         |
//| Tenta SR_<simbolo>.csv e, se nao existir, SR_<simbolo base>.csv   |
//| (cobre o sufixo que muitos brokers de FX acrescentam).            |
//+------------------------------------------------------------------+
string ResolverArquivo()
  {
   if(InpArquivo != "")
      return InpArquivo;

   int flag = InpPastaComum ? FILE_COMMON : 0;
   string simbolo = (InpSimbolo != "") ? InpSimbolo : _Symbol;

   string tentativas[2];
   tentativas[0] = InpPrefixo + SanitizarSimbolo(simbolo) + ".csv";
   tentativas[1] = InpPrefixo + SanitizarSimbolo(SimboloBase(simbolo)) + ".csv";

   for(int i = 0; i < 2; i++)
      if(tentativas[i] != "" && FileIsExist(tentativas[i], flag))
         return tentativas[i];

   return tentativas[0];   // devolve o nome esperado, para a mensagem de erro
  }

//+------------------------------------------------------------------+
//| Le o CSV inteiro. Devolve o numero de niveis ou -1 em erro.       |
//+------------------------------------------------------------------+
int LerArquivo(const string arquivo, Nivel &niveis[])
  {
   int flag = FILE_READ | FILE_TXT | FILE_ANSI | (InpPastaComum ? FILE_COMMON : 0);
   int h = FileOpen(arquivo, flag);
   if(h == INVALID_HANDLE)
     {
      PrintFormat("SR_Levels: nao consegui abrir '%s' (erro %d). "
                  "Rode o main.py do projeto SR-metatrader5 para gerar o arquivo.",
                  arquivo, GetLastError());
      return -1;
     }

   ArrayResize(niveis, 0);
   int linha = 0, lidos = 0, ignorados = 0;
   string simbolo_arquivo = "";

   while(!FileIsEnding(h) && lidos < SR_MAX_NIVEIS)
     {
      string texto = FileReadString(h);
      linha++;
      StringTrimLeft(texto);
      StringTrimRight(texto);
      if(texto == "")
         continue;

      string campos[];
      int n = StringSplit(texto, ';', campos);
      if(n < 3)
         continue;

      // cabecalho
      if(linha == 1 && campos[1] == "price")
         continue;

      if(simbolo_arquivo == "")
         simbolo_arquivo = campos[0];

      Nivel lv;
      lv.price       = StringToDouble(campos[1]);
      lv.score       = StringToDouble(campos[2]);
      lv.n_events    = (n > 3) ? (int)StringToInteger(campos[3]) : 0;
      lv.unique_days = (n > 4) ? (int)StringToInteger(campos[4]) : 0;
      lv.last_event  = (n > 8) ? StringToTime(campos[8]) : 0;

      if(lv.price <= 0.0)
         continue;
      if(InpScoreMinimo > 0.0 && lv.score < InpScoreMinimo)
        {
         ignorados++;
         continue;
        }

      int k = ArraySize(niveis);
      ArrayResize(niveis, k + 1);
      niveis[k] = lv;
      lidos++;
     }
   FileClose(h);

   if(lidos == 0)
     {
      PrintFormat("SR_Levels: '%s' nao tem nenhum nivel utilizavel "
                  "(%d descartados pelo score minimo %.1f).",
                  arquivo, ignorados, InpScoreMinimo);
      return -1;
     }

   if(InpConferirSimbolo && simbolo_arquivo != "" && !MesmoSimbolo(simbolo_arquivo, _Symbol))
     {
      PrintFormat("SR_Levels: '%s' contem niveis de %s, mas o grafico e de %s. "
                  "Nada foi desenhado (desligue 'Conferir simbolo' para forcar).",
                  arquivo, simbolo_arquivo, _Symbol);
      return -1;
     }

   if(ignorados > 0)
      PrintFormat("SR_Levels: %d niveis abaixo do score minimo %.1f foram ignorados.",
                  ignorados, InpScoreMinimo);
   return lidos;
  }

//+------------------------------------------------------------------+
//| Mantem so os InpMaxLinhas de maior score (selection sort parcial).|
//+------------------------------------------------------------------+
void LimitarPorScore(Nivel &niveis[], const int limite)
  {
   int n = ArraySize(niveis);
   if(limite <= 0 || n <= limite)
      return;

   for(int i = 0; i < limite; i++)
     {
      int melhor = i;
      for(int j = i + 1; j < n; j++)
         if(niveis[j].score > niveis[melhor].score)
            melhor = j;
      if(melhor != i)
        {
         Nivel tmp = niveis[i];
         niveis[i] = niveis[melhor];
         niveis[melhor] = tmp;
        }
     }
   ArrayResize(niveis, limite);
  }

//+------------------------------------------------------------------+
//| Apaga todas as linhas criadas por este indicador.                 |
//+------------------------------------------------------------------+
void LimparObjetos()
  {
   ObjectsDeleteAll(0, SR_PREFIXO, 0, OBJ_HLINE);
   g_desenhadas = 0;
  }

//+------------------------------------------------------------------+
//| Desenha as linhas.                                                |
//+------------------------------------------------------------------+
void Desenhar(Nivel &niveis[])
  {
   LimparObjetos();

   int n = ArraySize(niveis);
   for(int i = 0; i < n; i++)
     {
      string nome = StringFormat("%s%03d", SR_PREFIXO, i);
      if(!ObjectCreate(0, nome, OBJ_HLINE, 0, 0, niveis[i].price))
         continue;

      string texto = StringFormat("SR %s  R%.0f T%d",
                                  DoubleToString(niveis[i].price, _Digits),
                                  niveis[i].score, niveis[i].n_events);
      string dica = texto;
      if(niveis[i].last_event > 0)
         dica += StringFormat("  |  %d dias distintos  |  ultimo toque %s",
                              niveis[i].unique_days,
                              TimeToString(niveis[i].last_event, TIME_DATE));

      ObjectSetInteger(0, nome, OBJPROP_COLOR,      InpCor);
      ObjectSetInteger(0, nome, OBJPROP_WIDTH,      InpEspessura);
      ObjectSetInteger(0, nome, OBJPROP_STYLE,      InpEstilo);
      ObjectSetInteger(0, nome, OBJPROP_BACK,       InpAoFundo);
      ObjectSetInteger(0, nome, OBJPROP_SELECTABLE, InpSelecion);
      ObjectSetInteger(0, nome, OBJPROP_SELECTED,   false);
      ObjectSetInteger(0, nome, OBJPROP_HIDDEN,     false);
      ObjectSetInteger(0, nome, OBJPROP_ZORDER,     0);
      ObjectSetString(0, nome, OBJPROP_TEXT,    InpRotulo ? texto : "");
      ObjectSetString(0, nome, OBJPROP_TOOLTIP, dica);
     }
   g_desenhadas = n;
   ChartRedraw(0);
  }

//+------------------------------------------------------------------+
//| Carrega o arquivo e redesenha. `forcar` ignora a data de modific. |
//+------------------------------------------------------------------+
bool Recarregar(const bool forcar)
  {
   int flag = InpPastaComum ? FILE_COMMON : 0;
   g_arquivo = ResolverArquivo();

   if(!FileIsExist(g_arquivo, flag))
     {
      if(!g_avisado)
        {
         PrintFormat("SR_Levels: arquivo '%s' nao existe na pasta %s do terminal.",
                     g_arquivo, InpPastaComum ? "Common\\Files" : "MQL5\\Files");
         Comment(StringFormat("SR_Levels: %s nao encontrado", g_arquivo));
         g_avisado = true;
        }
      return false;
     }
   g_avisado = false;

   datetime mod = (datetime)FileGetInteger(g_arquivo, FILE_MODIFY_DATE, InpPastaComum);
   if(!forcar && mod == g_modificado)
      return false;                        // nada mudou desde a ultima leitura

   Nivel niveis[];
   int n = LerArquivo(g_arquivo, niveis);
   if(n <= 0)
     {
      g_modificado = mod;                  // nao insiste no mesmo arquivo quebrado
      LimparObjetos();
      ChartRedraw(0);
      return false;
     }

   LimitarPorScore(niveis, InpMaxLinhas);
   Desenhar(niveis);
   g_modificado = mod;

   PrintFormat("SR_Levels: %d niveis de '%s' desenhados em %s (arquivo de %s).",
               ArraySize(niveis), g_arquivo, _Symbol,
               TimeToString(mod, TIME_DATE | TIME_MINUTES));
   Comment("");
   return true;
  }

//+------------------------------------------------------------------+
//| OnInit                                                            |
//+------------------------------------------------------------------+
int OnInit()
  {
   IndicatorSetString(INDICATOR_SHORTNAME, "SR Levels");
   g_avisado = false;
   Recarregar(true);
   if(InpRecarregarSeg > 0)
      EventSetTimer((int)MathMax(1, InpRecarregarSeg));
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| OnDeinit                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   LimparObjetos();
   Comment("");
   ChartRedraw(0);
  }

//+------------------------------------------------------------------+
//| OnTimer -- so recarrega se o Python regravou o arquivo            |
//+------------------------------------------------------------------+
void OnTimer()
  {
   Recarregar(false);
  }

//+------------------------------------------------------------------+
//| OnCalculate -- o indicador nao tem buffers; as linhas sao objetos |
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
   // Se o grafico foi aberto antes do arquivo existir, tenta de novo na
   // primeira barra que chegar.
   if(g_desenhadas == 0 && prev_calculated == 0)
      Recarregar(true);
   return rates_total;
  }
//+------------------------------------------------------------------+
