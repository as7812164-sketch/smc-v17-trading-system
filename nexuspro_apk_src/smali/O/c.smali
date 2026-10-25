.class abstract LO/c;
.super Ljava/lang/Object;
.source "SourceFile"


# direct methods
.method public static a(LS/a;)LO/a;
    .locals 3

    .line 1
    const-string v0, "initializer"

    .line 2
    .line 3
    invoke-static {p0, v0}, LT/d;->e(Ljava/lang/Object;Ljava/lang/String;)V

    .line 4
    .line 5
    .line 6
    new-instance v0, LO/e;

    .line 7
    .line 8
    const/4 v1, 0x0

    .line 9
    const/4 v2, 0x2

    .line 10
    invoke-direct {v0, p0, v1, v2, v1}, LO/e;-><init>(LS/a;Ljava/lang/Object;ILT/b;)V

    .line 11
    .line 12
    .line 13
    return-object v0
.end method
