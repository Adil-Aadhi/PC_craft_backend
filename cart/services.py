def validate_build(data, products):
    notes = []

    cpu = products.get(data.get("cpu"))
    motherboard = products.get(data.get("motherboard"))
    ram = products.get(data.get("ram"))
    psu = products.get(data.get("psu"))
    gpu = products.get(data.get("gpu"))
    case = products.get(data.get("case"))
    case_fan = products.get(data.get("case_fan"))
    cooler = products.get(data.get("cooler"))

    is_compatible = True  # 🔥 master flag

    # CPU ↔ Motherboard
    if cpu and motherboard and hasattr(cpu, "cpu_spec") and hasattr(motherboard, "motherboard_spec"):
        if cpu.cpu_spec.socket != motherboard.motherboard_spec.socket:
            is_compatible = False
            notes.append("CPU and Motherboard socket mismatch")

    # RAM ↔ Motherboard
    if ram and motherboard and hasattr(ram, "ram_spec") and hasattr(motherboard, "motherboard_spec"):
        if ram.ram_spec.ram_type != motherboard.motherboard_spec.ram_type:
            is_compatible = False
            notes.append("RAM type not supported by motherboard")

    # Cooler ↔ CPU socket
    if cpu and cooler and hasattr(cpu, "cpu_spec") and hasattr(cooler, "cooler_spec"):
        supported = (cooler.cooler_spec.supported_sockets or "").split(",")
        if cpu.cpu_spec.socket not in supported:
            is_compatible = False
            notes.append("Cooler does not support CPU socket")

    # Cooler height vs Case
    if case and cooler and hasattr(case, "case_spec") and hasattr(cooler, "cooler_spec"):
        if case.case_spec.max_cpu_cooler_height_mm and cooler.cooler_spec.cooler_height_mm:
            if cooler.cooler_spec.cooler_height_mm > case.case_spec.max_cpu_cooler_height_mm:
                is_compatible = False
                notes.append("Cooler height exceeds case clearance")

    # PSU wattage
    total_watt = 0
    if cpu and hasattr(cpu, "cpu_spec"):
        total_watt += cpu.cpu_spec.tdp or 0

    if gpu and hasattr(gpu, "gpu_spec"):
        total_watt += gpu.gpu_spec.tdp or 0

    if psu and hasattr(psu, "psu_spec"):
        if psu.psu_spec.wattage < total_watt + 100:
            is_compatible = False
            notes.append("PSU wattage insufficient")

    # GPU length vs Case
    if case and gpu and hasattr(case, "case_spec") and hasattr(gpu, "gpu_spec"):
        if case.case_spec.max_gpu_length_mm and gpu.gpu_spec.length_mm:
            if gpu.gpu_spec.length_mm > case.case_spec.max_gpu_length_mm:
                is_compatible = False
                notes.append("GPU too long for case")

    # Case fan → warning only
    if case and case_fan:
        notes.append("Case fan compatibility not fully validated for this case")

    return is_compatible, ", ".join(notes)