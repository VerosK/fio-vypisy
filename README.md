# FIO Výpisy 

If you can't understand the language, then the repository
is probably not intended for you. It contains a Python script 
for automating access to Czech Fio bank.


## K čemu to je?

Každý měsíc bych měl stáhnout výpisy z Fio banky, roztřídit je a poslat
kolegyni ke zpracování. 

Naštěstí FIO banka má API, takže se to celá půlhodinová práce
dá zkrátit na 5 minut.

## Použití

 * okopírovat `tokens.ini.example` na `tokens.ini`
 * doplnit Read-Only tokeny z FIO banky do `tokens.ini` a případně přidat
   nějaké sekce s dalšími účty a jejich tokeny.
 * získat přístupy k nějakému SMTP serveru (AWS SES, Google Mail, Mailgun)   
   a vložit je do `tokens.ini`
 * spustit skript

## Co to dělá?

1. stáhne GPC PDF a CSV výpisy z banky do adresáře
2. zabalí je do ZIP souboru
3. pošle ZIP soubor na zadanou adresu

## Problémy

 * FIO banka má omezení na 2 dotazy za minutu. Pokud skript spadne 
   na 429 (Too Many Requests), tak je stačí počkat 30 vteřin a
   spustit znovu.
 * FIO banka praděpodobně generuje PDF verzi výpisu minulého měsíce první 
   den následujícího měsíce. Pokud skript spadne na 404 (Not Found) nebo na
   500 (Error), obvykle stačí počkat 86400 vteřin a spustit znovu.
 * Pokud na účtu není daný měsíc žádný pohyb, tak FIO banka výpis ani nevygeneruje
   a skript pak spadne na 404 (Not Found). Asi by to šlo detekovat, nicméně
   bylo jednodušší nastavit trvalý příkaz, který jednou za měsíc z každého 
   účtu pošle korunu či euro na jiný účet.

## License

Skript je prost jakékoliv záruky a podpory. It works on my laptop™.

CC0 or WTFPL
