          
        df = detect_signals(df)
        last = df.iloc[-1]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if last["final_sell"]:
            msg = f"⚠️ SELL sinyali - {sym} ({INTERVAL})\nRSI: {last['rsi']:.1f}  Vol: {last['v']:.0f}"
            print(msg)
            notify_telegram(msg)
            results.append((sym, "SELL"))
        elif last["final_buy"]:
            msg = f"✅ BUY sinyali - {sym} ({INTERVAL})\nRSI: {last['rsi']:.1f}  Vol: {last['v']:.0f}"
            print(msg)
            notify_telegram(msg)
            results.append((sym, "BUY"))

        time.sleep(0.5)  # API limitine saygı

    print(f"\nToplam sinyal: {len(results)} coin bulundu.")
    for s, t in results:
        print(f"→ {s}: {t}")

if __name__ == "__main__":
    main()
